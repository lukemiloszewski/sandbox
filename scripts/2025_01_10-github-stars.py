import base64
import os
from contextlib import contextmanager
from datetime import datetime

import dotenv
from github import Github
from pydantic import BaseModel
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)

dotenv.load_dotenv()


class GithubRepo(BaseModel):
    """Pydantic model for GitHub repository data."""

    name: str
    description: str | None = None
    url: str
    language: str | None = None
    stars: int
    date: str
    readme: str | None = None


class GithubUser(BaseModel):
    """Pydantic model for GitHub user data."""

    username: str
    avatar_url: str | None = None
    name: str | None = None


metadata = MetaData()

tbl_users = Table(
    "tbl_users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String, nullable=False, unique=True),
    Column("avatar_url", String),
    Column("name", String),
    Column("created_at", String, nullable=False),
)

tbl_repositories = Table(
    "tbl_repositories",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("tbl_users.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("url", String),
    Column("language", String),
    Column("stars", Integer),
    Column("date", String),
    Column("readme", Text),
    Column("inserted_at", String),
)


class DatastoreRepository:
    """Repository pattern implementation for database operations."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.init_database()

    def init_database(self):
        metadata.create_all(self.engine, checkfirst=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        with self.engine.connect() as connection:
            yield connection
            connection.commit()

    def save_repos(
        self, user: GithubUser, repos: list[GithubRepo], inserted_at: str
    ) -> None:
        """
        Save multiple repositories to database for a given user.

        Args:
            user: GithubUser containing user information
            repos: List of repositories to save
            inserted_at: Timestamp for when these repositories were inserted
        """
        with self.get_connection() as conn:
            user_id = self._get_user_id(user)

            for repo in repos:
                stmt = tbl_repositories.insert().values(
                    user_id=user_id,
                    name=repo.name,
                    description=repo.description,
                    url=repo.url,
                    language=repo.language,
                    stars=repo.stars,
                    date=repo.date,
                    readme=repo.readme,
                    inserted_at=inserted_at,
                )
                conn.execute(stmt)

    def fetch_repos(self, user: GithubUser) -> list[GithubRepo]:
        """
        Fetch all repositories from the latest insert date for a specific user.

        Args:
            user: GithubUser object containing user information

        Returns:
            List[GithubRepo]: List of repositories as GithubRepo instances
        """
        with self.get_connection() as conn:
            user_id = self._get_user_id(user)

            if not user_id:
                return []

            query = (
                select(tbl_repositories)
                .where(tbl_repositories.c.user_id == user_id)
                .where(
                    tbl_repositories.c.inserted_at
                    == select(tbl_repositories.c.inserted_at)
                    .where(tbl_repositories.c.user_id == user_id)
                    .order_by(tbl_repositories.c.inserted_at.desc())
                    .limit(1)
                    .scalar_subquery()
                )
            )

            result = conn.execute(query)

            return [
                GithubRepo(
                    name=row.name,
                    description=row.description,
                    url=row.url,
                    language=row.language,
                    stars=row.stars,
                    date=row.date,
                    readme=row.readme,
                )
                for row in result
            ]

    def _get_user_id(self, user: GithubUser) -> int:
        """
        Get user ID from database, creating the user if they don't exist.

        Args:
            user: GithubUser containing user information

        Returns:
            int: Database ID for the user
        """
        with self.get_connection() as conn:
            query = select(tbl_users).where(tbl_users.c.username == user.username)
            result = conn.execute(query).first()

            if result:
                return result.id

            stmt = tbl_users.insert().values(
                username=user.username,
                avatar_url=user.avatar_url,
                name=user.name,
                created_at=datetime.now().isoformat(),
            )
            result = conn.execute(stmt)
            return result.inserted_primary_key[0]


class GithubRepository:
    """Repository for fetching GitHub data."""

    def __init__(self, client: Github):
        self.client = client

    @staticmethod
    def _get_readme_content(repo) -> str | None:
        """Fetch README content for a repository."""
        try:
            readme = repo.get_readme()
            return base64.b64decode(readme.content).decode("utf-8")
        except Exception:
            return None

    def get_user_info(self, username: str) -> GithubUser:
        """
        Fetch user information for a given GitHub username.

        Args:
            username: GitHub username to fetch information for

        Returns:
            GithubUser: User information
        """
        user = self.client.get_user(username)
        return GithubUser(
            username=user.login,
            avatar_url=user.avatar_url,
            name=user.name,
        )

    def get_starred_repos(self, user: GithubUser, limit: int = 10) -> list[GithubRepo]:
        """
        Fetch starred repositories for a given GitHub user.

        Args:
            user: GithubUser containing user information
            limit: Maximum number of repositories to fetch

        Returns:
            List[GithubRepo]: List of starred repositories
        """
        github_user = self.client.get_user(user.username)
        stars = github_user.get_starred()

        repositories = []
        for i, repo in enumerate(stars):
            if i >= limit:
                break

            print(f"Fetching data for {repo.full_name} ({i+1}/{limit})...")

            repo_data = GithubRepo(
                name=repo.full_name,
                description=repo.description,
                url=repo.html_url,
                language=repo.language,
                stars=repo.stargazers_count,
                date=repo.created_at.isoformat(),
                readme=self._get_readme_content(repo),
            )
            repositories.append(repo_data)

        return repositories


def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        exit(1)

    # clients
    github_client = Github(token)
    github_repo = GithubRepository(github_client)
    datastore_repo = DatastoreRepository("sqlite:///github_stars.db")

    # github user
    target_username = "lukemiloszewski"
    user = github_repo.get_user_info(target_username)

    print(f"Querying repositories for {user.username}...")
    repositories = github_repo.get_starred_repos(user, limit=10)

    print("\nSaving repositories to database...")
    inserted_at = datetime.now().isoformat()
    datastore_repo.save_repos(user, repositories, inserted_at)

    print("\nFetching repositories:")
    latest_repos = datastore_repo.fetch_repos(user)
    for repo in latest_repos:
        print(f"- {repo.name}")


if __name__ == "__main__":
    main()

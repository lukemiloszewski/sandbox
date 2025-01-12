import base64
import os
from contextlib import contextmanager
from datetime import datetime

import dotenv
from github import Github
from pydantic import BaseModel
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)

dotenv.load_dotenv()


class GithubRepoModel(BaseModel):
    """Pydantic model for GitHub repository data."""

    name: str
    description: str | None = None
    url: str
    language: str | None = None
    stars: int
    date: str
    readme: str | None = None


metadata = MetaData()

repositories = Table(
    "repositories",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
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

    def save_repositories(self, repos: list[GithubRepoModel], inserted_at: str) -> None:
        """Save multiple repositories to database."""
        with self.get_connection() as conn:
            for repo in repos:
                stmt = repositories.insert().values(
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

    def get_latest_repositories(self) -> list[GithubRepoModel]:
        """
        Get all repositories from the latest insert date.

        Returns:
            List[GithubRepoModel]: List of repositories as GithubRepoModel instances
        """
        with self.get_connection() as conn:
            query = select(repositories).where(
                repositories.c.inserted_at
                == select(repositories.c.inserted_at)
                .order_by(repositories.c.inserted_at.desc())
                .limit(1)
                .scalar_subquery()
            )
            result = conn.execute(query)

            return [
                GithubRepoModel(
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

    def get_starred_repos(self, limit: int = 10) -> list[GithubRepoModel]:
        """Fetch starred repositories from GitHub."""
        user = self.client.get_user()
        stars = user.get_starred()

        repositories = []
        for i, repo in enumerate(stars):
            if i >= limit:
                break

            print(f"Fetching data for {repo.full_name} ({i+1}/{limit})...")

            repo_data = GithubRepoModel(
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
    # authentication
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        exit(1)

    # github client
    github_client = Github(token)
    github_repo = GithubRepository(github_client)

    # datastore client
    datastore_repo = DatastoreRepository("sqlite:///github_stars.db")

    print("Fetching starred repositories...")
    repositories = github_repo.get_starred_repos(limit=10)
    inserted_at = datetime.now().isoformat()

    print("\nSaving repositories to database...")
    datastore_repo.save_repositories(repositories, inserted_at)

    print("\nLatest repositories:")
    latest_repos = datastore_repo.get_latest_repositories()
    for repo in latest_repos:
        print(f"- {repo.name}")


if __name__ == "__main__":
    main()

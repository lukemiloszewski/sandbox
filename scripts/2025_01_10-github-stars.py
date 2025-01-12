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
    starred_at: str
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
    Column("starred_at", String),
    Column("readme", Text),
    Column("fetch_date", String),
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

    def save_repositories(self, repos: list[GithubRepoModel], fetch_date: str) -> None:
        """Save multiple repositories to database."""
        with self.get_connection() as conn:
            for repo in repos:
                stmt = repositories.insert().values(
                    name=repo.name,
                    description=repo.description,
                    url=repo.url,
                    language=repo.language,
                    stars=repo.stars,
                    starred_at=repo.starred_at,
                    readme=repo.readme,
                    fetch_date=fetch_date,
                )
                conn.execute(stmt)

    def get_fetch_stats(self, fetch_date: str) -> dict:
        """Get statistics for a specific fetch date."""
        with self.get_connection() as conn:
            total_repos = conn.execute(
                select(repositories).where(repositories.c.fetch_date == fetch_date).count()
            ).scalar()

            readme_count = conn.execute(
                select(repositories)
                .where(repositories.c.fetch_date == fetch_date)
                .where(repositories.c.readme.is_not(None))
                .count()
            ).scalar()

            return {"total_repos": total_repos, "readme_count": readme_count}

    def get_repositories_by_language(self, language: str) -> list[dict]:
        """Get all repositories for a specific language."""
        with self.get_connection() as conn:
            query = select(repositories).where(repositories.c.language == language)
            return [dict(row) for row in conn.execute(query)]

    def get_most_starred_repos(self, limit: int = 10) -> list[dict]:
        """Get top N most starred repositories."""
        with self.get_connection() as conn:
            query = select(repositories).order_by(repositories.c.stars.desc()).limit(limit)
            return [dict(row) for row in conn.execute(query)]

    def get_latest_fetch_date(self) -> str | None:
        """Get the most recent fetch date."""
        with self.get_connection() as conn:
            query = (
                select(repositories.c.fetch_date)
                .order_by(repositories.c.fetch_date.desc())
                .limit(1)
            )
            return conn.execute(query).scalar()


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
                starred_at=repo.created_at.isoformat(),
                readme=self._get_readme_content(repo),
            )
            repositories.append(repo_data)

        return repositories


def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        exit(1)

    # Initialize repositories
    github_client = Github(token)
    github_repo = GithubRepository(github_client)
    datastore_repo = DatastoreRepository("sqlite:///github_stars.db")

    # Fetch and store data
    print("Starting to fetch first 10 starred repositories...")
    repositories = github_repo.get_starred_repos(limit=10)
    fetch_date = datetime.now().isoformat()

    datastore_repo.save_repositories(repositories, fetch_date)
    stats = datastore_repo.get_fetch_stats(fetch_date)

    print(f"\nSaved {stats['total_repos']} starred repositories to github_stars.db")
    print(f"Successfully fetched READMEs for {stats['readme_count']} repositories")

    # Example of using other repository methods
    print("\nMost starred repositories:")
    for repo in datastore_repo.get_most_starred_repos(limit=5):
        print(f"- {repo['name']}: {repo['stars']} stars")


if __name__ == "__main__":
    main()

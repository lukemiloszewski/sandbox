import base64
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import chromadb
import dotenv
from chromadb.api.client import Client
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

    def save_repos(self, user: GithubUser, repos: list[GithubRepo], inserted_at: str) -> None:
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


class VectorDatastoreRepository:
    """Repository for managing vector embeddings of GitHub repositories."""

    def __init__(self, client: Client, collection_name: str):
        """
        Initialize the vector datastore repository.

        Args:
            client: ChromaDB client instance
            collection_name: Name of the ChromaDB collection to use
        """
        self.client = client
        self.collection_name = collection_name

        self.collection = self.client.get_or_create_collection(collection_name)

    def _create_document_from_repo(self, repo: GithubRepo) -> str:
        """
        Create a document string from a GitHub repository.

        Args:
            repo: GithubRepo instance to convert to document

        Returns:
            str: Combined document text
        """
        doc_parts = [
            f"Repository: {repo.name}",
            f"Description: {repo.description}" if repo.description else "",
            f"Language: {repo.language}" if repo.language else "",
            f"README: {repo.readme}" if repo.readme else "",
        ]

        return " ".join(filter(None, doc_parts))

    def add_repos(self, user: GithubUser, repos: list[GithubRepo]) -> None:
        """
        Add repositories to the vector store.

        Args:
            user: GithubUser instance
            repos: List of GithubRepo instances to store
        """
        if not repos:
            return

        documents = [self._create_document_from_repo(repo) for repo in repos]
        ids = [f"{user.username}_{repo.name}_{hash(repo.url)}" for repo in repos]
        metadatas = [
            {
                "username": user.username or "",
                "user_name": user.name or "",
                "repo_name": repo.name or "",
                "repo_url": repo.url or "",
                "repo_language": repo.language or "",
                "repo_stars": repo.stars or "",
                "repo_date": repo.date or "",
            }
            for repo in repos
        ]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def query_repos(
        self,
        query_text: str,
        n_results: int = 5,
        filters: dict[str, Any] | None = None,
        document_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Query the vector store for similar repositories.

        Args:
            query_text: Text to search for
            n_results: Number of results to return
            filters: Optional metadata filters (e.g., {"username": "example"})
            document_filter: Optional document content filter (e.g., {"$contains": "python"})

        Returns:
            Dictionary containing query results directly from ChromaDB
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filters,
            where_document=document_filter,
        )

    def delete_collection(self) -> None:
        """Delete the current collection."""
        self.client.delete_collection(self.collection_name)


def run_datastore(github_repo, datastore_repo, github_username, n_limit=1000):
    # fetch user from github
    user = github_repo.get_user_info(github_username)

    # fetch repositories from github
    print(f"Querying repositories for {user.username}...")
    repositories = github_repo.get_starred_repos(user, limit=n_limit)

    # save repositories to database
    print("\nSaving repositories to database...")
    inserted_at = datetime.now().isoformat()
    datastore_repo.save_repos(user, repositories, inserted_at)


def run_vectorstore(github_repo, vectorstore_repo, github_username):
    # fetch user from github
    user = github_repo.get_user_info(github_username)

    # fetch latest repositories from database
    print("\nFetching repositories:")
    latest_repos = datastore_repo.fetch_repos(user)
    for repo in latest_repos:
        print(f"- {repo.name}")

    print("\nAdding repositories to vector store...")
    vectorstore_repo.add_repos(user, latest_repos)


def query_vectorstore(github_repo, vectorstore_repo, github_username, query, n_limit=20):
    # fetch user from github
    user = github_repo.get_user_info(github_username)

    results = vectorstore_repo.query_repos(
        query, filters={"username": user.username}, n_results=n_limit
    )

    print(f"\nResults for: '{query}':")
    for i, doc_id in enumerate(results["ids"][0]):
        print(
            f"- {results['metadatas'][0][i]['repo_name']} "
            f"(Distance: {results['distances'][0][i]:.4f})"
        )


if __name__ == "__main__":
    # authentication
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        exit(1)

    # github client
    github_client = Github(token)
    github_repo = GithubRepository(github_client)

    # datastore client
    datastore_repo = DatastoreRepository("sqlite:///.temp/github_stars.db")

    # vector store client
    chroma_client = chromadb.PersistentClient(path=".temp/chroma_data")
    vectorstore_repo = VectorDatastoreRepository(
        client=chroma_client, collection_name="github_repos"
    )

    # run_datastore(github_repo, datastore_repo, "lukemiloszewski", n_limit=1)
    # run_vectorstore(github_repo, vectorstore_repo, "lukemiloszewski")

    queries = [
        # "build llms using agents",
        # "cli tools for terminal productivity",
        # "quant finance",
        # "portfolio optimisation",
        # "invoke multiple llms and synthesise answers",
        "tool for htop or tree or terminal utilities on system monitoring",
    ]
    for query in queries:
        query_vectorstore(github_repo, vectorstore_repo, "lukemiloszewski", query, n_limit=20)

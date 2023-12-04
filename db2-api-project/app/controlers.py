from litestar import Controller, get, patch, post
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.exceptions import HTTPException
from datetime import datetime, timedelta

from app.dtos import (
    AuthorReadDTO,
    AuthorReadFullDTO,
    AuthorUpdateDTO,
    AuthorWriteDTO,
    BookReadDTO,
    BookWriteDTO,
    ClientReadDTO,
    ClientWriteDTO,
    LoanReadDTO,
)

from app.models import Author, Book, Client, Loan
from app.repositories import (
    AuthorRepository,
    BookRepository,
    ClientRepository,
    LoanRepository,
    provide_authors_repo,
    provide_books_repo,
    provide_clients_repo,
    provide_loans_repo,
)


class AuthorController(Controller):
    path = "/authors"
    tags = ["authors"]
    return_dto = AuthorReadDTO
    dependencies = {"authors_repo": Provide(provide_authors_repo)}

    @get()
    async def list_authors(self, authors_repo: AuthorRepository) -> list[Author]:
        return authors_repo.list()

    @post(dto=AuthorWriteDTO)
    async def create_author(self, data: Author, authors_repo: AuthorRepository) -> Author:
        return authors_repo.add(data)

    @get("/{author_id:int}", return_dto=AuthorReadFullDTO)
    async def get_author(self, author_id: int, authors_repo: AuthorRepository) -> Author:
        author = authors_repo.get(author_id)
        if not author:
            raise HTTPException(404, detail="El autor no existe")
        return author

    @patch("/{author_id:int}", dto=AuthorUpdateDTO)
    async def update_author(
        self, author_id: int, data: DTOData[Author], authors_repo: AuthorRepository
    ) -> Author:
        author = authors_repo.get(author_id)
        if not author:
            raise HTTPException(404, detail="El autor no existe")
        author = data.update_instance(author)
        return authors_repo.update(author)


class BookController(Controller):
    path = "/books"
    tags = ["books"]
    return_dto = BookReadDTO
    dependencies = {"books_repo": Provide(provide_books_repo)}

    @get()
    async def list_books(self, books_repo: BookRepository) -> list[Book]:
        books = books_repo.list()
        if not books:
            raise HTTPException(404, detail="No hay libros disponibles")
        return books

    @get("/{book_id:int}", return_dto=BookReadDTO)
    async def get_book(self, book_id: int, books_repo: BookRepository) -> Book:
        book = books_repo.get(book_id)
        if not book:
            raise HTTPException(404, detail="El libro no existe")
        return book

    @patch("/{book_id:int}", dto=BookWriteDTO)
    async def update_book(
        self, book_id: int, data: DTOData[Book], books_repo: BookRepository
    ) -> Book:
        book = books_repo.get(book_id)
        if not book:
            raise HTTPException(404, detail="El libro no existe")
        book = data.update_instance(book)
        return books_repo.update(book)

    @get("/search", return_dto=BookReadDTO)
    async def search_books(self, title: str, books_repo: BookRepository) -> list[Book]:
        books = books_repo.search_by_title(title)
        if not books:
            raise HTTPException(404, detail="No se encontraron libros con ese título")
        return books


class ClientController(Controller):
    path = "/clients"
    tags = ["clients"]
    return_dto = ClientReadDTO
    dependencies = {"clients_repo": Provide(provide_clients_repo)}

    @get()
    async def list_clients(self, clients_repo: ClientRepository) -> list[Client]:
        clients = clients_repo.list()
        if not clients:
            raise HTTPException(404, detail="No hay clientes disponibles")
        return clients

    @post(dto=ClientWriteDTO)
    async def create_client(self, data: Client, clients_repo: ClientRepository) -> Client:
        return clients_repo.add(data)


class LoanController(Controller):
    path = "/loans"
    tags = ["loans"]
    return_dto = LoanReadDTO
    dependencies = {"loans_repo": Provide(provide_loans_repo)}

    @post("/{book_id:int}/{client_id:int}")
    async def create_loan(
        self,
        book_id: int,
        client_id: int,
        loans_repo: LoanRepository,
        books_repo: BookRepository,
        clients_repo: ClientRepository,
    ) -> Loan:
        book = books_repo.get(book_id)
        client = clients_repo.get(client_id)

        if not book or not client:
            raise HTTPException(404, detail="El libro o el cliente no existe")

        if books_repo.is_book_available(book_id):
            raise HTTPException(400, detail="No hay copias disponibles para préstamo")

        loan_date = datetime.utcnow()
        loan = Loan(book_id=book_id, client_id=client_id, loan_date=loan_date)
        loans_repo.add(loan)

        return loan

    @patch("/{loan_id:int}/return")
    async def return_loan(
        self,
        loan_id: int,
        loans_repo: LoanRepository,
    ) -> Loan:
        loan = loans_repo.get(loan_id)

        if not loan:
            raise HTTPException(404, detail="El préstamo no existe")

        if loan.return_date:
            raise HTTPException(400, detail="El libro ya ha sido devuelto")

        return_date = datetime.utcnow()
        loan.return_date = return_date

        due_date = loan.loan_date + timedelta(days=7)
        if return_date > due_date:
            days_overdue = (return_date - due_date).days
            loan.fine = days_overdue * 0.5

        return loans_repo.update(loan)
from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

Id = Annotated[int, Field(strict=True, gt=0, le=2147483647)]
Money = Annotated[
    Decimal, Field(ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False)
]
Name = Annotated[str, Field(min_length=2, max_length=100)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CategoriaInput(Input):
    nome: Name


class ClienteInput(Input):
    nome: Name
    email: Annotated[
        str, Field(min_length=5, max_length=150, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    ]
    telefone: Annotated[str, Field(max_length=20)] | None = None


class ProdutoInput(Input):
    nome: Annotated[str, Field(min_length=2, max_length=150)]
    preco: Money
    categoria_id: Id
    # Estoque entra pela rota de entradas, gerando histórico desde o cadastro.


class Produto(BaseModel):
    id: int
    nome: str
    preco: Decimal
    estoque: int
    categoria_id: int


class QuantidadeInput(Input):
    quantidade: Id


class ItemInput(QuantidadeInput):
    produto_id: Id


class PedidoInput(Input):
    cliente_id: Id
    itens: Annotated[list[ItemInput], Field(min_length=1, max_length=100)]
    desconto: Money = Decimal("0.00")
    frete: Money = Decimal("0.00")

    @field_validator("itens")
    @classmethod
    def produtos_unicos(cls, itens):
        if len({item.produto_id for item in itens}) != len(itens):
            raise ValueError("Produto repetido no pedido")
        return itens


class ItemPedido(BaseModel):
    produto_id: int
    produto: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal


class Pedido(BaseModel):
    id: int
    cliente_id: int
    data_pedido: date
    status: str
    desconto: Decimal
    frete: Decimal
    subtotal: Decimal
    total: Decimal
    itens: list[ItemPedido]

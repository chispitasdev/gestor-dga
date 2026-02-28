"""Excepciones de dominio del sistema DGA.

Define las excepciones especificas del negocio que permiten distinguir
errores de logica de dominio de errores genericos de infraestructura.
Cada excepcion hereda de una clase base comun ``DGADomainError`` para
facilitar el manejo centralizado.
"""


class DGADomainError(Exception):
    """Clase base para todas las excepciones de dominio DGA."""


class TransformerNotFoundError(DGADomainError):
    """Se lanza cuando no se encuentra un transformador solicitado.

    Attributes:
        transformer_id: Identificador buscado.
    """

    def __init__(self, transformer_id: int) -> None:
        self.transformer_id = transformer_id
        super().__init__(
            f"No se encontro el transformador con ID {transformer_id}."
        )


class SampleNotFoundError(DGADomainError):
    """Se lanza cuando no se encuentra una muestra solicitada.

    Attributes:
        sample_id: Identificador buscado.
    """

    def __init__(self, sample_id: int) -> None:
        self.sample_id = sample_id
        super().__init__(
            f"No se encontro la muestra con ID {sample_id}."
        )


class DuplicateTransformerError(DGADomainError):
    """Se lanza al intentar registrar un transformador con nombre duplicado.

    Attributes:
        name: Nombre duplicado.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"Ya existe un transformador con el nombre '{name}'."
        )


class DuplicateSampleCodeError(DGADomainError):
    """Se lanza al intentar registrar una muestra con codigo duplicado.

    Attributes:
        sample_code: Codigo duplicado.
    """

    def __init__(self, sample_code: str) -> None:
        self.sample_code = sample_code
        super().__init__(
            f"Ya existe una muestra con el codigo '{sample_code}'."
        )


class InvalidGasValueError(DGADomainError):
    """Se lanza cuando un valor de concentracion de gas es invalido.

    Puede ocurrir si el valor es negativo o no es numerico.
    """

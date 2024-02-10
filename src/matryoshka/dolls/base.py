import abc


class DollsBase(abc.ABC):
    @property
    @abc.abstractmethod
    def maximum_capacity(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def encode(self, secret_text: bytes) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> bytes:
        raise NotImplementedError

    def accept_size(self, size: int) -> bool:
        return self.maximum_capacity == 0 or size <= self.maximum_capacity


class DollError(ValueError):
    pass

"""Abstract base classes."""
import logging
import pickle

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from numbers import Real
from rich.logging import RichHandler
from typing import Any, Callable, Optional


logger = logging.getLogger(__name__)

rich_handler = RichHandler()
rich_handler.setLevel(logging.DEBUG)
rich_handler.setFormatter(logging.Formatter('%(message)s'))

logger.addHandler(rich_handler)


class _SerializableMixin:

    def serialize(self) -> bytes:
        """Return the serialized representation of the object.

        Returns
        -------
        bytes
            Serialized representation of the object.

        """
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, serialized: bytes):
        """Construct a class instance from its serialized representation.

        Parameters
        ----------
        serialized : bytes
            Serialized representation of the object.

        Returns
        -------
        cls
            The deserialized object.

        """
        obj = pickle.loads(serialized)
        if not isinstance(obj, cls):
            raise TypeError(f'object must be an instance of {cls}')
        return obj

    def save(self, file: str):
        """Save the object to a file.

        Parameters
        ----------
        file : str
            Path of the file to which to save the object.

        """
        with open(file, 'wb') as f:
            f.write(self.serialize())

    @classmethod
    def load(cls, file: str):
        """Load a class instance from a file.

        Parameters
        ----------
        file : str
            Path of the file from which to load the object.

        Returns
        -------
        cls
            The object loaded from `file`.

        """
        with open(file, 'rb') as f:
            return cls.deserialize(f.read())


class SynDModel(_SerializableMixin, ABC):
    """Abstract base class for SynD models."""

    logger = logger

    def __init__(self, default_backmapper: Optional[Callable] = None):
        self._backmappers = {}
        if default_backmapper is not None:
            self.default_backmapper = default_backmapper

    @property
    def default_backmapper(self) -> Optional[Callable]:
        return self._backmappers.get('default')

    @default_backmapper.setter
    def default_backmapper(self, value: Callable):
        self.add_backmapper(value, 'default')

    def add_backmapper(self, backmapper: Callable, name: str):
        if name in self._backmappers:
            msg = f'a backmapper named {name!r} is already defined for this model'
            raise ValueError(msg)
        self._backmappers[name] = backmapper

    def remove_backmapper(self, name: str):
        if name not in self._backmappers:
            msg = f'no backmapper named {name!r} is defined for this model'
            raise ValueError(msg)
        self._backmappers.pop(name)

    def get_backmapper(self, name: str) -> Callable:
        if name not in self._backmappers:
            msg = f'no backmapper named {name!r} is defined for this model'
            raise ValueError(msg)
        return self._backmappers[name]

    @abstractmethod
    def generate_unmapped_trajectories(
            self,
            length: Real,
            initial_states: Iterable,
            **kwargs,
    ) -> Iterable:
        ...

    def generate_trajectories(
            self,
            length: Real,
            initial_states: Iterable,
            backmapper: Optional[str] = 'default',
            **kwargs,
    ) -> Iterator:
        if backmapper is not None:
            backmapper = self.get_backmapper(backmapper)
        for traj in self.generate_unmapped_trajectories(length, initial_states, **kwargs):
            if backmapper is not None:
                traj = backmapper(traj)
            yield traj

    def generate_trajectory(
            self,
            length: Real,
            initial_state: Any,
            backmapper: Optional[str] = 'default',
            **kwargs,
    ):
        return next(iter(self.generate_trajectories(
            length,
            initial_states=[initial_state],
            backmapper=backmapper,
            **kwargs,
        )))

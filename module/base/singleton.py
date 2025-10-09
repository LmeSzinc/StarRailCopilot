import threading
from typing import Type, TypeVar

T = TypeVar('T')


class Singleton(type):
    """
    A metaclass for creating a global singleton.

    Any class using this metaclass will have only one instance.
    Subclasses will have their own unique singleton instance.
    This implementation is thread-safe.
    """

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls.__instances = None
        cls.__lock = threading.Lock()

    def __call__(cls: Type[T], *args, **kwargs) -> T:
        # return cached instance directly
        instance = cls.__instances
        if instance is not None:
            return instance

        # create new instance
        with cls.__lock:
            # another thread may have created while we are waiting
            instance = cls.__instances
            if instance is not None:
                return instance

            # create
            instance = super().__call__(*args, **kwargs)
            cls.__instances = instance
            return instance

    def singleton_clear_all(cls):
        """
        Remove all instances
        """
        with cls.__lock:
            cls.__instances = None


class SingletonNamed(type):
    """
    A metaclass for creating a named singleton.

    Instances are created based on the first argument provided to the constructor.
    Each class will have its own separate cache of named instances.
    This implementation is thread-safe.
    """

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls.__instances = {}
        cls.__lock = threading.Lock()

    def __call__(cls: Type[T], name, *args, **kwargs) -> T:
        # return cached instance directly
        try:
            return cls.__instances[name]
        except KeyError:
            pass

        # create new instance
        with cls.__lock:
            # another thread may have created while we are waiting
            try:
                return cls.__instances[name]
            except KeyError:
                pass

            # create
            instance = super().__call__(name, *args, **kwargs)
            cls.__instances[name] = instance
            return instance

    def singleton_remove(cls, name):
        """
        Remove a specific instance.
        Instance will be re-created, the nest time it is requested.

        Returns:
            bool: If removed
        """
        # delete from dict is threadsafe
        try:
            del cls.__instances[name]
            return True
        except KeyError:
            return False

    def singleton_clear_all(cls):
        """
        Remove all instances
        """
        with cls.__lock:
            cls.__instances.clear()

    def singleton_instances(cls):
        """
        Access all instances directly

        Returns:
            dict:
        """
        return cls.__instances

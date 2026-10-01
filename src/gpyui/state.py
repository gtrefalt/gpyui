"""Explicit, event-driven state binding; no attribute polling."""

from collections.abc import Callable


class State[T]:
    """Observable application state. Mutate on the app's callback thread while running."""

    def __init__(self, value: T):
        self._value = value
        self._observers: dict[object, Callable[[T], None]] = {}

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        if self._value == value:
            return
        self._value = value
        for observer in tuple(self._observers.values()):
            observer(value)

    def subscribe(self, observer: Callable[[T], None]) -> Callable[[], None]:
        """Observe replacements; return an idempotent unsubscribe function."""
        key = object()
        self._observers[key] = observer

        def unsubscribe() -> None:
            self._observers.pop(key, None)

        return unsubscribe

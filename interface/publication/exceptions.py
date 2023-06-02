class PublicationException:

    _message: str = ""
    _prefix: str = ""
    _postfix: str = ""

    @staticmethod
    def throw(prefix: str, message: str, postfix: str) -> str:
        return f"{prefix}{message}{postfix}"


class RequiredFieldException:

    @staticmethod
    def throw(prefix: str, message: str, postfix: str) -> str:
        return f"{prefix} The field \'{message}\' is required {postfix}"


class UnknownFieldException:

    @staticmethod
    def throw(prefix: str, message: str, postfix: str) -> str:
        return f"{prefix} The field \'{message}\' does not exist in table \'{postfix}\'"


class NoFieldException:

    @staticmethod
    def throw(prefix: str, message: str, postfix: str) -> str:
        return f"{prefix} The model \'{message}\' has no fields {postfix}"


class LocationUndefined:

    @staticmethod
    def throw(prefix: str, message: str, postfix: str) -> str:
        return f"{prefix} location of the {message} is undefined in {postfix}"

"""
Custom exception hierarchy for MedFabric API.
"""


class MedFabricError(Exception):
    """Base class for all MedFabric API errors."""


# --- Session-related errors ---
class SessionError(MedFabricError):
    """Base class for session-related errors."""


class InvalidUUIDError(SessionError):
    """Raised when an invalid UUID is provided."""


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""


class SessionInactiveError(SessionError):
    """Raised when a session is not active or expired."""


class SessionMismatchError(SessionError):
    """Raised when a session does not match the expected criteria."""


class SessionAlreadyExistsError(SessionError):
    """Raised when a session already exists for a given doctor."""


# --- Authentication & Authorization ---
class AuthError(MedFabricError):
    """Base class for authentication/authorization errors."""


class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""


class UserNotFoundError(AuthError):
    """Raised when a user is not found."""


class UnauthorizedError(AuthError):
    """Raised when a doctor tries to access a resource they don't own."""


# --- Database layer ---
class DatabaseError(MedFabricError):
    """Base class for database-related errors."""


class DuplicateEntryError(DatabaseError):
    """Raised when attempting to insert a duplicate record."""


class ConstraintViolationError(DatabaseError):
    """Raised when a database constraint is violated (foreign key, etc.)."""


# --- ImageSet domain ---
class ImageSetError(MedFabricError):
    """Base class for image set-related errors."""


class InvalidImageSetError(ImageSetError):
    """Raised when an image set is invalid or does not meet criteria."""


class ImageSetNotFoundError(ImageSetError):
    """Raised when an image set is not found."""


class ImageSetAlreadyExistsError(ImageSetError):
    """Raised when an image set with the same ID already exists."""


class InvalidImageSetPathError(ImageSetError):
    """Raised when an image set has an invalid or non-existent folder path."""


# --- Patient domain ---
class PatientError(MedFabricError):
    """Base class for patient-related errors."""


class PatientNotFoundError(PatientError):
    """Raised when a patient is not found."""


class PatientAlreadyExistsError(PatientError):
    """Raised when a patient with the same ID already exists."""


class PatientInvalidDataError(PatientError):
    """Raised when patient data is invalid or incomplete."""


# --- Evaluation domain ---
class EvaluationError(MedFabricError):
    """Base class for evaluation-related errors."""


class EvaluationAlreadyExistsError(EvaluationError):
    """Raised when an evaluation already exists for doctor/session/imageset."""


class EvaluationNotFoundError(EvaluationError):
    """Raised when an evaluation is not found."""


class InvalidEvaluationError(EvaluationError):
    """Raised when an evaluation is invalid or does not meet criteria."""


# --- Image domain ---
class ImageError(MedFabricError):
    """Base class for image-related errors."""


class InvalidImageError(ImageError):
    """Raised when an image is invalid or does not meet criteria."""


class ImageNotFoundError(ImageError):
    """Raised when an image is not found."""


class ImageAlreadyExistsError(ImageError):
    """Raised when an image with the same ID already exists."""


# --- Runtime domain ---
class EmptyDatasetError(MedFabricError):
    """Raised when a dataset is empty or contains no valid entries."""

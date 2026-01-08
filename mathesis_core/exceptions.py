
class MathesisBaseException(Exception):
    """Base exception for Mathesis application"""
    pass

class CrawlerException(MathesisBaseException):
    """Base exception for crawler errors"""
    pass

class SchoolNotFoundError(CrawlerException):
    """Raised when a school cannot be found"""
    pass

class CrawlerTimeoutError(CrawlerException):
    """Raised when crawling times out"""
    pass

class ETLException(MathesisBaseException):
    """Base exception for ETL errors"""
    pass

class ValidationError(ETLException):
    """Raised when data validation fails"""
    pass

class LoadError(ETLException):
    """Raised when data loading fails"""
    pass

class RAGException(MathesisBaseException):
    """Base exception for RAG errors"""
    pass

class ExportException(MathesisBaseException):
    """Base exception for Export/Report errors"""
    pass

from rest_framework.pagination import PageNumberPagination


class LimitePaginaPagination(PageNumberPagination):
    """Permite pedir más filas por página con ?page_size=N."""
    page_size_query_param = 'page_size'
    max_page_size = 1000

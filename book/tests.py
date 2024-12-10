from django.test import TestCase, Client
from unittest.mock import patch, Mock
from django.urls import reverse


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data



class BookSearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.search_url = reverse('book:book_search')

    @patch('requests.get')
    def test_book_search_with_query_and_free_books(self, mock_get):
        # Create a mock response with two free books
        mock_response = {
            'totalItems': 2,
            'items': [{
                'volumeInfo': {
                    'title': 'Free Test Book 1',
                    'authors': ['Author 1'],
                    'description': 'A free test book',
                    'imageLinks': {'thumbnail': 'http://example.com/thumb.jpg'},
                    'infoLink': 'http://example.com/book',
                    'previewLink': 'http://example.com/preview',
                    'publisher': 'Test Publisher',
                    'publishedDate': '2024-01-01'
                }
            }, {
                'volumeInfo': {
                    'title': 'Free Test Book 2',
                    'authors': ['Author 2'],
                    'description': 'Another free test book',
                    'imageLinks': {'thumbnail': 'http://example.com/thumb2.jpg'},
                    'infoLink': 'http://example.com/book2',
                    'previewLink': 'http://example.com/preview2',
                    'publisher': 'Test Publisher',
                    'publishedDate': '2024-01-01'
                }
            }]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        response = self.client.get('/book/search/?q=test&book_type=free')

        books = response.context['book']
        self.assertEqual(len(books), 2)  

    @patch('requests.get')
    def test_book_search_with_query_and_paid_books(self, mock_get): 
        mock_response = {
            'totalItems': 2,
            'items': [{
                'volumeInfo': {
                    'title': 'Paid Test Book 1',
                    'authors': ['Paid Author'],
                    'description': 'A paid test book',
                    'imageLinks': {'thumbnail': 'http://example.com/thumb.jpg'},
                    'infoLink': 'http://example.com/book',
                    'previewLink': 'http://example.com/preview',
                    'publisher': 'Paid Publisher',
                    'publishedDate': '2024-01-01'
                }
            }, {
                'volumeInfo': {
                    'title': 'Paid Test Book 2',
                    'authors': ['Paid Author 2'],
                    'description': 'Another paid test book',
                    'imageLinks': {'thumbnail': 'http://example.com/thumb2.jpg'},
                    'infoLink': 'http://example.com/book2',
                    'previewLink': 'http://example.com/preview2',
                    'publisher': 'Paid Publisher',
                    'publishedDate': '2024-01-01'
                }
            }]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        response = self.client.get('/book/search/?q=test&book_type=paid')

        books = response.context['book']
        self.assertEqual(len(books), 2)  # Check if the response contains 2 books

    def test_book_search_no_query(self):
        response = self.client.get(self.search_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'book_search.html')
        self.assertIn('books', response.context)
        self.assertEqual(len(response.context['books']), 0)


class BookDetailViewTest(TestCase):
    @patch('requests.get')
    def test_book_detail_view(self, mock_get):
        book_id = 'test_book_id'
        mock_response_data = {
            'volumeInfo': {
                'title': 'Test Book Detail',
                'authors': ['Author Detail'],
                'description': 'Detail Description',
                'imageLinks': {'thumbnail': 'http://example.com/detail_thumbnail.jpg'},
                'infoLink': 'http://example.com/detail',
                'previewLink': 'http://example.com/preview_detail',
                'publisher': 'Detail Publisher',
                'publishedDate': '2024-01-03',
            }
        }
        mock_get.return_value = MockResponse(mock_response_data, 200)

        response = self.client.get(reverse('book:book_detail', args=[book_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'book_detail.html')
        self.assertIn('book', response.context)
        self.assertEqual(response.context['book']['volumeInfo']['title'], 'Test Book Detail')

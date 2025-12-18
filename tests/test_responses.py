##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for protocol responses
##

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communication.protocol.responses import (
    ResponseType,
    Response,
    OkResponse,
    ErrorResponse,
    UnknownResponse,
    MoveResponse,
    AboutResponse,
)


class TestResponses:
    def test_response_creation(self):
        response = Response(ResponseType.OK, "test data")
        assert response.type == ResponseType.OK
        assert response.data == "test data"

    def test_response_to_output_with_data(self):
        response = Response(ResponseType.ERROR, "error message")
        assert response.to_output() == "ERROR error message"

    def test_response_to_output_without_data(self):
        response = Response(ResponseType.OK)
        assert response.to_output() == "OK"

    def test_ok_response(self):
        response = OkResponse()
        assert response.type == ResponseType.OK
        assert response.data is None
        assert response.to_output() == "OK"

    def test_error_response(self):
        response = ErrorResponse("Board too large")
        assert response.type == ResponseType.ERROR
        assert response.data == "Board too large"
        assert response.to_output() == "ERROR Board too large"

    def test_unknown_response(self):
        response = UnknownResponse("Command not supported")
        assert response.type == ResponseType.UNKNOWN
        assert response.data == "Command not supported"
        assert response.to_output() == "UNKNOWN Command not supported"

    def test_unknown_response_without_message(self):
        response = UnknownResponse()
        assert response.type == ResponseType.UNKNOWN
        assert response.data is None
        assert response.to_output() == "UNKNOWN"

    def test_move_response(self):
        response = MoveResponse(10, 15)
        assert response.type == ResponseType.MOVE
        assert response.data == "10,15"
        assert response.x == 10
        assert response.y == 15
        assert response.to_output() == "10,15"

    def test_about_response_full_info(self):
        response = AboutResponse(
            name="TestBrain",
            version="2.0",
            author="TestAuthor",
            country="US",
            www="http://test.com",
            email="test@test.com"
        )
        expected = 'name="TestBrain", version="2.0", author="TestAuthor", country="US", www="http://test.com", email="test@test.com"'
        assert response.to_output() == expected

    def test_about_response_minimal_info(self):
        response = AboutResponse(name="TestBrain", version="1.0", author="TestAuthor")
        expected = 'name="TestBrain", version="1.0", author="TestAuthor", country="FR"'
        assert response.to_output() == expected

    def test_about_response_default_values(self):
        response = AboutResponse()
        output = response.to_output()
        assert 'name="Gomokucaracha"' in output
        assert 'version="6.7"' in output
        assert 'author="Santiago Eliott Paul-Antoine"' in output
        assert 'country="FR"' in output

    def test_about_response_partial_defaults(self):
        response = AboutResponse(name="CustomBrain")
        output = response.to_output()
        assert 'name="CustomBrain"' in output
        assert 'version="6.7"' in output  # default
        assert 'author="Santiago Eliott Paul-Antoine"' in output    # default
        assert 'country="FR"' in output   # default

    def test_response_type_enum_values(self):
        assert ResponseType.OK.value == "OK"
        assert ResponseType.ERROR.value == "ERROR"
        assert ResponseType.UNKNOWN.value == "UNKNOWN"
        assert ResponseType.MOVE.value == "MOVE"
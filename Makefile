##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Makefile
##

NAME = pbrain-gomoku-ai

SRC_DIR = src
MAIN_FILE = main.py

all: $(NAME)

$(NAME): $(SRC_DIR)/$(MAIN_FILE)
	ln -s $(SRC_DIR)/$(MAIN_FILE) $(NAME)
	chmod +x $(NAME)

binary: $(SRC_DIR)/$(MAIN_FILE)
	pyinstaller --onefile --name $(NAME) \
		--add-data "$(SRC_DIR):." \
		$(SRC_DIR)/$(MAIN_FILE)
	mv dist/$(NAME) binary_gomokucaracha

clean:
	rm -rf build dist *.spec

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re binary

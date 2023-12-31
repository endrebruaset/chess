from game import Game
from board import Board
from piece import Piece, PieceColor, PieceType
from square import Square
from move import Move, MoveType
from typing import Optional
from enum import Enum

class Result(Enum):
    WHITE_WIN = 0,
    BLACK_WIN = 1
    STALEMATE = 2,
    INSUFFICIENT_MATERIAL = 3  

class GameRules:
    @staticmethod
    def get_legal_moves(game: Game) -> list[Move]:
        legal_moves = []
        
        # Psuedo legal moves not exposing the king to a check
        psuedo_legal_moves = GameRules.__get_psuedo_legal_moves(game)
        for move in psuedo_legal_moves:
            if not GameRules.is_check(game.simulate_move(move), king_color=game.turn):
                legal_moves.append(move)
        
        # Castling moves
        legal_moves.extend(GameRules.__get_castling_moves(game))
        
        return legal_moves
    
    @staticmethod
    def is_check(board: Board, king_color: PieceColor) -> bool:
        opponent_color = PieceColor.opposing_color(king_color)
        attacked_squares = GameRules.__get_attacked_squares(board, opponent_color)
        
        # Get king position
        king_square = None
        for square in board.get_squares_with_pieces(king_color):
            piece = board[square]
            if piece is not None and piece.type == PieceType.KING:
                king_square = square
        
        if king_square is None:
            raise ValueError('Board has no king')
        
        # King is in check if attacked by opposing pieces
        return king_square in attacked_squares
    
    @staticmethod
    def get_game_result(game: Game) -> Optional[Result]:
        # Game is over if there are no legal moves
        # Get result
        if len(GameRules.get_legal_moves(game)) == 0:
            if GameRules.is_check(game.board, game.turn):
                return Result.WHITE_WIN if game.turn == PieceColor.BLACK else Result.BLACK_WIN
            else:
                return Result.STALEMATE
            
        # Check for insufficient material
        white_pieces = [game.board[square] for square in game.board.get_squares_with_pieces(PieceColor.WHITE)]
        black_pieces = [game.board[square] for square in game.board.get_squares_with_pieces(PieceColor.BLACK)]
        if GameRules.__is_insufficient_material(white_pieces) and GameRules.__is_insufficient_material(black_pieces):
            return Result.INSUFFICIENT_MATERIAL
        
        return None
    
    @staticmethod
    def __get_psuedo_legal_moves(game: Game) -> list[Move]:
        squares_with_own_pieces = game.board.get_squares_with_pieces(game.turn)
        
        psuedo_legal_moves = []
        for square in squares_with_own_pieces:
            piece = game.board[square]
            psuedo_legal_moves.extend(
                GameRules.__get_psuedo_legal_moves_for_piece(piece, square, game.board, game.en_passant)
            )
        
        return psuedo_legal_moves
    
    @staticmethod
    def __get_psuedo_legal_moves_for_piece(piece: Piece, start_square: Square, board: Board, en_passant: Square = None) -> list[Move]:
        psuedo_legal_moves = []
        
        opponent_color = PieceColor.opposing_color(piece.color)
        squares_with_opponent_pieces = board.get_squares_with_pieces(opponent_color)
        if en_passant is not None:
            squares_with_opponent_pieces.append(en_passant)
            
        empty_squares = board.get_empty_squares()
        
        match piece.type:
            case PieceType.PAWN:
                direction = Board.get_pawn_direction(piece.color)
                one_row_forward = start_square.row + direction
                move_type = MoveType.PAWN_PROMOTION if one_row_forward == Board.get_pawn_end_row(piece.color) else MoveType.ORDINARY
                        
                # Captures               
                capture_squares = [
                    Square(one_row_forward, start_square.column - 1),
                    Square(one_row_forward, start_square.column + 1)
                ]
                for capture_square in capture_squares:
                    if capture_square in squares_with_opponent_pieces:
                        psuedo_legal_moves.append(Move(start_square, capture_square, move_type))
                
                # One square forward
                one_square_forward = Square(one_row_forward, start_square.column)
                if one_square_forward in empty_squares:
                    psuedo_legal_moves.append(Move(start_square, one_square_forward, move_type))
                    
                    # Two squares forward
                    starting_row = Board.get_pawn_starting_row(piece.color)
                    two_squares_forward = Square(one_row_forward + direction, start_square.column)
                    if start_square.row == starting_row and two_squares_forward in empty_squares:
                        psuedo_legal_moves.append(Move(start_square, two_squares_forward, MoveType.DOUBLE_PAWN_PUSH))
            
            case PieceType.KNIGHT:
                moves = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
                available_squares = empty_squares + squares_with_opponent_pieces
                
                for move in moves:
                    end_square = Square(start_square.row + move[0], start_square.column + move[1])
                    if end_square in available_squares:
                        psuedo_legal_moves.append(Move(start_square, end_square))
            
            case PieceType.BISHOP:
                directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
                for direction in directions:
                    psuedo_legal_moves.extend(
                        GameRules.__get_ranged_piece_psuedo_legal_moves_in_direction(direction, start_square, empty_squares, squares_with_opponent_pieces)
                    )
            
            case PieceType.ROOK:
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                for direction in directions:
                    psuedo_legal_moves.extend(
                        GameRules.__get_ranged_piece_psuedo_legal_moves_in_direction(direction, start_square, empty_squares, squares_with_opponent_pieces)
                    )
            
            case PieceType.QUEEN:
                psuedo_legal_moves.extend(
                    GameRules.__get_psuedo_legal_moves_for_piece(Piece(piece.color, PieceType.BISHOP), start_square, board) +
                    GameRules.__get_psuedo_legal_moves_for_piece(Piece(piece.color, PieceType.ROOK), start_square, board)
                )                
            
            case PieceType.KING:
                moves = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
                available_squares = empty_squares + squares_with_opponent_pieces
                
                for move in moves:
                    end_square = Square(start_square.row + move[0], start_square.column + move[1])
                    if end_square in available_squares:
                        psuedo_legal_moves.append(Move(start_square, end_square))
            
        return psuedo_legal_moves
    
    @staticmethod
    def __get_castling_moves(game: Game) -> list[Move]:
        if GameRules.is_check(game.board, game.turn):
            return []
        
        empty_squares = game.board.get_empty_squares()
        opponent_attacked_squares = GameRules.__get_attacked_squares(game.board, PieceColor.opposing_color(game.turn))
        valid_castling_square = lambda square: square in empty_squares and square not in opponent_attacked_squares
        
        castling_moves = []
        starting_row = Board.get_pawn_end_row(PieceColor.opposing_color(game.turn))
        
        if game.long_castling_rights[game.turn]:
            long_castling_squares = [Square(starting_row, 1), Square(starting_row, 2), Square(starting_row, 3)]
            if all([valid_castling_square(square) for square in long_castling_squares]):
                castling_moves.extend([
                    Move(Square(starting_row, 4), Square(starting_row, 0), MoveType.LONG_CASTLE),
                    Move(Square(starting_row, 4), Square(starting_row, 1), MoveType.LONG_CASTLE),
                    Move(Square(starting_row, 4), Square(starting_row, 2), MoveType.LONG_CASTLE)
                ])
            
        if game.short_castling_rights[game.turn]:
            short_castling_squares = [Square(starting_row, 5), Square(starting_row, 6)]
            if all([valid_castling_square(square) for square in short_castling_squares]):
                castling_moves.extend([
                    Move(Square(starting_row, 4), Square(starting_row, 6), MoveType.SHORT_CASTLE),
                    Move(Square(starting_row, 4), Square(starting_row, 7), MoveType.SHORT_CASTLE)
                ])
        
        return castling_moves
        
    @staticmethod
    def __get_attacked_squares(board: Board, turn: PieceColor) -> list[Square]:
        squares_with_own_pieces = board.get_squares_with_pieces(turn)
        
        attacked_squares = []
        for square in squares_with_own_pieces:
            piece = board[square]
            if piece.type == PieceType.PAWN:
                direction = Board.get_pawn_direction(piece.color)           
                capture_squares = [
                    Square(square.row + direction, square.column - 1),
                    Square(square.row + direction, square.column + 1)
                ]
                
                attacked_squares.extend([square for square in capture_squares if square.is_valid()])
                
            else:
                attacked_squares.extend([
                    move.end for move in GameRules.__get_psuedo_legal_moves_for_piece(piece, square, board)
                ])
        
        return attacked_squares
    
    @staticmethod
    def __is_insufficient_material(pieces: list[Piece]) -> bool:
        if len(pieces) > 2:
            return False
        
        piece_types = set([piece.type for piece in pieces])
        return piece_types == set([PieceType.KING]) or \
            piece_types == set([PieceType.KING, PieceType.KNIGHT]) or \
            piece_types == set([PieceType.KING, PieceType.BISHOP])
    
    @staticmethod
    def __get_ranged_piece_psuedo_legal_moves_in_direction(
        direction: tuple[int, int], 
        start_square: Square, 
        empty_squares: list[Square], 
        squares_with_opponent_pieces: list[Square]
    ) -> list[Move]:
        psuedo_legal_moves = []

        steps = 1
        while True:
            end_square = Square(start_square.row + direction[0]*steps, start_square.column + direction[1]*steps)
            if end_square in empty_squares:
                psuedo_legal_moves.append(Move(start_square, end_square))
                steps += 1
            
            elif end_square in squares_with_opponent_pieces:
                psuedo_legal_moves.append(Move(start_square, end_square))
                break
            
            else:
                break

        return psuedo_legal_moves
        
from enum import IntEnum, IntFlag
from functools import partial, reduce
from operator import or_, add


class Square(IntEnum):
    a8, b8, c8, d8, e8, f8, g8, h8, \
    a7, b7, c7, d7, e7, f7, g7, h7, \
    a6, b6, c6, d6, e6, f6, g6, h6, \
    a5, b5, c5, d5, e5, f5, g5, h5, \
    a4, b4, c4, d4, e4, f4, g4, h4, \
    a3, b3, c3, d3, e3, f3, g3, h3, \
    a2, b2, c2, d2, e2, f2, g2, h2, \
    a1, b1, c1, d1, e1, f1, g1, h1 = range(64)


class Bitboard(IntFlag):
    a8, b8, c8, d8, e8, f8, g8, h8, \
    a7, b7, c7, d7, e7, f7, g7, h7, \
    a6, b6, c6, d6, e6, f6, g6, h6, \
    a5, b5, c5, d5, e5, f5, g5, h5, \
    a4, b4, c4, d4, e4, f4, g4, h4, \
    a3, b3, c3, d3, e3, f3, g3, h3, \
    a2, b2, c2, d2, e2, f2, g2, h2, \
    a1, b1, c1, d1, e1, f1, g1, h1 = (1 << i for i in range(64))


class File(IntEnum):
    a, b, c, d, e, f, g, h = range(8)


class Rank(IntEnum):
    _8, _7, _6, _5, _4, _3, _2, _1 = range(8)


class PieceType(IntEnum):
    p, n, b, r, q, k = range(6)


class Color(IntEnum):
    w, b = 0, 1


class Piece(IntEnum):
    P, N, B, R, Q, K, p, n, b, r, q, k = range(12)


class CastlingSide(IntEnum):
    K, Q = 0, 1


class Castling(IntEnum):
    K, Q, k, q = range(4)


class CastlingAbility(IntFlag):
    K, Q, k, q = 1, 2, 4, 8


def square_from(file: File, rank: Rank):
    return Square(rank << 3 | file)


def file_of(square: Square):
    return File(square & 7)


def rank_of(square: Square):
    return Rank(square >> 3)


def piece_from(piece_type: PieceType, color: Color):
    return Piece(color * 6 + piece_type)


def piece_type_of(piece: Piece):
    return PieceType(piece % 6)


def color_of(piece: Piece):
    return Color(piece // 6)


def bitboard_from(square: Square):
    return Bitboard(1 << square)


def castling_from(castling_side: CastlingSide, color: Color):
    return Castling(color << 1 | castling_side)


def castling_ability_from(castling: Castling):
    return CastlingAbility(1 << castling)


class MoveFlag(IntFlag):
    en_passant, promotion, special_1, special_0 = 8, 4, 2, 1


class Move:

    def __init__(self,
                 from_square: Square,
                 to_square: Square,
                 flag: MoveFlag = MoveFlag(0)):
        self.from_square = from_square
        self.to_square = to_square
        self.flag = flag

    def __str__(self):
        uci = self.from_square.name + self.to_square.name
        if MoveFlag.promotion in self.flag:
            special_0 = MoveFlag.special_0 in self.flag
            uci += ('q' if special_0 else
                    'r') if MoveFlag.special_1 in self.flag else (
                        'b' if special_0 else 'n')
        return uci


class Board:

    def __init__(
            self,
            fen:
        str = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        try:
            piece_placement, \
            side_to_move, \
            castling_ability, \
            en_passant_target_square, \
            halfmove_clock, \
            fullmove_counter = fen.split()
        except ValueError:
            raise ValueError(f'Invalid FEN: {fen}')
        self.piece_type_bitboards = [Bitboard(0)] * 6
        self.color_bitboards = [Bitboard(0)] * 2
        for rank, rank_placement in zip(Rank, piece_placement.split('/')):
            file = 0
            for ch in rank_placement:
                if ch.isdigit():
                    file += int(ch)
                else:
                    self.place(getattr(Piece, ch), square_from(file, rank))
                    file += 1
        self.side_to_move = getattr(Color, side_to_move)
        self.castling_ability = CastlingAbility(
            0) if castling_ability == '-' else reduce(
                or_, map(partial(getattr, CastlingAbility), castling_ability))
        self.en_passant_target_square = Bitboard(
            0) if en_passant_target_square == '-' else getattr(
                Bitboard, en_passant_target_square)
        self.halfmove_clock = int(halfmove_clock)
        self.fullmove_counter = int(fullmove_counter)

    def piece_bitboard(self, piece: Piece):
        return self.color_bitboards[color_of(
            piece)] & self.piece_type_bitboards[piece_type_of(piece)]

    def _str_board(self):
        board = [' '] * 64
        for piece in Piece:
            for square in self.piece_bitboard(piece):
                board[square.bit_length() - 1] = piece.name
        return ''.join(board)

    def __str__(self):
        board = self._str_board()
        return '╔═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╗\n' + '╠═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╣\n'.join(
            '║ ' + ' ║ '.join(board[square_from(file, rank)]
                              for file in File) + ' ║\n'
            for rank in Rank) + '╚═══╩═══╩═══╩═══╩═══╩═══╩═══╩═══╝\n'

    def to_fen(self):
        board = self._str_board()

        def _convert_spaces_to_digit(s: str):
            for n in range(8, 0, -1):
                s = s.replace(' ' * n, str(n))
            return s

        return ' '.join(
            ('/'.join(
                _convert_spaces_to_digit(board[rank << 3:rank + 1 << 3])
                for rank in Rank), self.side_to_move.name,
             reduce(
                 add,
                 map(lambda castling_ability: castling_ability.name,
                     self.castling_ability)) if self.castling_ability else '-',
             self.en_passant_target_square.name if
             self.en_passant_target_square else '-', str(self.halfmove_clock),
             str(self.fullmove_counter)))

    def place(self, piece: Piece, square: Square):
        square_bitboard = bitboard_from(square)
        self.piece_type_bitboards[piece_type_of(piece)] |= square_bitboard
        self.color_bitboards[color_of(piece)] |= square_bitboard

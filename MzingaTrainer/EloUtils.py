import math

DefaultRating = 1200
MinRating = 100

ProvisionalK = 64.0
DefaultK = 32.0


class EloUtils:

    @staticmethod
    def update_ratings(white_rating, black_rating, white_score, black_score, white_k=DefaultK, black_k=DefaultK):
        if white_rating < MinRating:
            raise ValueError("Invalid white_rating.")

        if black_rating < MinRating:
            raise ValueError("Invalid black_rating.")

        if white_score < 0.0 or white_score > 1.0:
            raise ValueError("Invalid white_score.")

        if black_score < 0.0 or black_score > 1.0:
            raise ValueError("Invalid black_score.")

        if white_k <= 0.0:
            raise ValueError("Invalid white_k.")

        if black_k <= 0.0:
            raise ValueError("Invalid black_k.")

        q_white = math.pow(10, white_rating / 400.0)
        q_black = math.pow(10, black_rating / 400.0)

        e_white = q_white / (q_white + q_black)
        e_black = q_black / (q_white + q_black)

        updated_white_rating = max(MinRating, white_rating + round(white_k * (white_score - e_white)))
        updated_black_rating = max(MinRating, black_rating + round(black_k * (black_score - e_black)))

        return updated_white_rating, updated_black_rating

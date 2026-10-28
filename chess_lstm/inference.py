
import numpy as np

from engine.legal_moves import generate_legal_moves
from engine.san import san_to_move


def predict_candidate_moves(
    board,
    history,
    model,
    tokenizer,
    sequence_length,
    top_k=5,
):
    """Return high-probability legal SAN moves."""

    if top_k <= 0:
        return []

    encoded = tokenizer.encode(history)
    encoded = encoded[-sequence_length:]

    inputs = np.zeros((1, sequence_length), dtype=np.int32)

    if encoded:
        inputs[0, -len(encoded):] = encoded

    probabilities = np.asarray(
        model.predict(inputs, verbose=0)
    )[0]

    legal_moves = set(generate_legal_moves(board))

    # Only inspect the highest-probability token IDs.
    k = min(len(probabilities), max(top_k * 20, top_k))

    if k == 0:
        return []

    candidate_ids = np.argpartition(
        probabilities, -k
    )[-k:]

    candidate_ids = candidate_ids[
        np.argsort(probabilities[candidate_ids])[::-1]
    ]

    legal_candidates = []

    id_to_token = tokenizer.id_to_token

    for token_id in candidate_ids:
        san = id_to_token.get(int(token_id), tokenizer.UNKNOWN_TOKEN)

        if san in (tokenizer.PAD_TOKEN, tokenizer.UNKNOWN_TOKEN):
            continue

        try:
            move = san_to_move(board, san)
        except (ValueError, IndexError, TypeError):
            continue

        if move not in legal_moves:
            continue

        legal_candidates.append(
            (san, move, float(probabilities[token_id]))
        )

        if len(legal_candidates) >= top_k:
            break

    return legal_candidates

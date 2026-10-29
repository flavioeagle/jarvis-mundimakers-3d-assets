"""Clipes de estado dos agentes (Idle, Working, AwaitingApproval, Done) sobre o rig de chibi.BONES.

posture="stand" | "sit"; work = "type" | "scan" | "inspect". Graus em XYZ local do osso:
- ossos verticais (coluna, cabeca): +X inclina para frente, +Y gira para a esquerda do personagem.
- bracos/pernas (apontando para baixo): -X leva para frente; braco esquerdo abre com -Z, direito com +Z.
- root: location em Y local = altura.
"""
import math

import chibi as C

SIT_DROP = 0.17
SIT = {
    "root": [(0, 0, 0), (0, -SIT_DROP, 0)],
    "thigh.L": [(-88, 0, -4)], "thigh.R": [(-88, 0, 4)],
    "shin.L": [(88, 0, 0)], "shin.R": [(88, 0, 0)],
}


def _blink(frames, at):
    return [(1, (0, 0, 0), None, (1, 1, 1)), (at, (0, 0, 0), None, (1, 1, 1)),
            (at + 3, (0, 0, 0), None, (1, 1, 0.08)), (at + 6, (0, 0, 0), None, (1, 1, 1)),
            (frames, (0, 0, 0), None, (1, 1, 1))]


def _hold(frames, rot, loc=None):
    return [(1, rot, loc), (frames, rot, loc)]


def _with_base(keys, frames, posture):
    if posture != "sit":
        return keys
    for bone, base in SIT.items():
        if bone in keys:
            continue
        if bone == "root":
            keys[bone] = _hold(frames, base[0], base[1])
        else:
            keys[bone] = _hold(frames, base[0])
    return keys


def make_clips(arm, posture="stand", work="type", wave="R", look_yaw=0.0):
    sit = posture == "sit"
    drop = (0, -SIT_DROP, 0) if sit else (0, 0, 0)
    blink = _blink(72, 46)

    idle = {
        "chest": [(1, (0, 0, 0)), (36, (2.5, 0, 0)), (72, (0, 0, 0))],
        "head": [(1, (0, -3, 0)), (36, (2, 3, 1.5)), (72, (0, -3, 0))],
        "upperarm.L": _hold(72, (-25, 0, -4) if sit else (0, 0, -6)),
        "upperarm.R": _hold(72, (-25, 0, 4) if sit else (0, 0, 6)),
        "eye.L": blink, "eye.R": blink,
    }
    if sit:
        idle["forearm.L"] = _hold(72, (-45, 0, 8))
        idle["forearm.R"] = _hold(72, (-45, 0, -8))
    else:
        idle["hips"] = [(1, (0, 0, -1.5)), (36, (0, 0, 1.5)), (72, (0, 0, -1.5))]
    C.make_action(arm, "Idle", 72, _with_base(idle, 72, posture))

    b48 = _blink(48, 22)
    if work == "type":
        tl = [(f, (-55 + (7 if (f // 6) % 2 else 0), 0, 6)) for f in range(1, 49, 6)] + [(48, (-55, 0, 6))]
        tr = [(f, (-55 + (0 if (f // 6) % 2 else 7), 0, -6)) for f in range(1, 49, 6)] + [(48, (-55, 0, -6))]
        working = {
            "spine": _hold(48, (6, 0, 0)),
            "head": [(1, (10, 0, 0)), (24, (8, 6, 0)), (48, (10, 0, 0))],
            "upperarm.L": _hold(48, (-38, 0, 8)), "upperarm.R": _hold(48, (-38, 0, -8)),
            "forearm.L": tl, "forearm.R": tr,
        }
    elif work == "scan":
        sweep = [(f, (-35, 0, -8 + 16 * math.sin(f / 48 * 2 * math.pi))) for f in range(1, 49, 6)] + [(48, (-35, 0, -8))]
        working = {
            "spine": _hold(48, (10, 0, 0)),
            "head": [(1, (16, 0, 0)), (24, (18, -4, 0)), (48, (16, 0, 0))],
            "upperarm.R": _hold(48, (-50, 0, -6)), "forearm.R": sweep,
            "upperarm.L": _hold(48, (-42, 0, 10)), "forearm.L": _hold(48, (-38, 0, 0)),
        }
    else:  # inspect: olha e aponta para a maquina a esquerda do personagem
        tool = [(f, (-62 + 18 * math.sin(f / 48 * 4 * math.pi), 0, -6)) for f in range(1, 49, 4)] + [(48, (-62, 0, -6))]
        working = {
            "spine": _hold(48, (4, 22, 0)),
            "head": [(1, (6, 18, 0)), (24, (10, 24, 0)), (48, (6, 18, 0))],
            "upperarm.L": [(1, (-75, 0, -12)), (24, (-82, 0, -12)), (48, (-75, 0, -12))],
            "forearm.L": _hold(48, (-12, 0, 0)),
            "upperarm.R": _hold(48, (-40, 0, 0)), "forearm.R": tool,
        }
    working["eye.L"] = working["eye.R"] = b48
    C.make_action(arm, "Working", 48, _with_base(working, 48, posture))

    s = 1 if wave == "R" else -1
    w = f"{'R' if s > 0 else 'L'}"
    o = "L" if w == "R" else "R"
    wav = [(f, (-15 + 12 * math.sin(f / 72 * 4 * math.pi), 0, s * 95)) for f in range(1, 73, 6)] + [(72, (-15, 0, s * 95))]
    awaiting = {
        "spine": _hold(72, (0, look_yaw * 0.5, s * 3)),
        "head": [(1, (-4, look_yaw * 0.5, s * 8)), (36, (-4, look_yaw * 0.5, s * 11)), (72, (-4, look_yaw * 0.5, s * 8))],
        f"upperarm.{w}": _hold(72, (-25, 0, s * 55)),
        f"forearm.{w}": wav,
        f"upperarm.{o}": _hold(72, (-25 if sit else -10, 0, -s * 6)),
        f"forearm.{o}": _hold(72, (-50, 0, 0)),
        "brow.L": _hold(72, (0, 0, 0), (0, 0, 0.006)), "brow.R": _hold(72, (0, 0, 0), (0, 0, 0.006)),
        "eye.L": _blink(72, 50), "eye.R": _blink(72, 50),
    }
    if not sit:
        awaiting[f"foot.{o}"] = [(f, (10 if (f // 12) % 2 else 0, 0, 0)) for f in range(1, 73, 12)] + [(72, (0, 0, 0))]
    C.make_action(arm, "AwaitingApproval", 72, _with_base(awaiting, 72, posture))

    hop = 0.012 if sit else 0.045
    happy_eye = [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.05, 1, 0.55)),
                 (40, (0, 0, 0), None, (1.05, 1, 0.55)), (48, (0, 0, 0), None, (1, 1, 1))]
    done = {
        "root": [(1, (0, 0, 0), drop), (12, (0, 0, 0), (0, drop[1] + hop, 0)), (24, (0, 0, 0), drop), (48, (0, 0, 0), drop)],
        "upperarm.L": [(1, (0, 0, -20)), (12, (0, 0, -150)), (40, (0, 0, -150)), (48, (0, 0, -20))],
        "upperarm.R": [(1, (0, 0, 20)), (12, (0, 0, 150)), (40, (0, 0, 150)), (48, (0, 0, 20))],
        "forearm.L": [(1, (0, 0, 0)), (12, (0, 0, -20)), (48, (0, 0, 0))],
        "forearm.R": [(1, (0, 0, 0)), (12, (0, 0, 20)), (48, (0, 0, 0))],
        "head": [(1, (0, 0, 0)), (12, (-10, 0, 0)), (40, (-10, 0, 0)), (48, (0, 0, 0))],
        "mouth": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.35, 1, 2.2)),
                  (40, (0, 0, 0), None, (1.35, 1, 2.2)), (48, (0, 0, 0), None, (1, 1, 1))],
        "eye.L": happy_eye, "eye.R": happy_eye,
    }
    C.make_action(arm, "Done", 48, _with_base(done, 48, posture), loop=False)

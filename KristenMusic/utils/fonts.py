"""Unicode 'fancy fonts'. Pure text, works in every Telegram chat (no parse_mode needed)."""
import string

_U, _L, _D = string.ascii_uppercase, string.ascii_lowercase, string.digits


def _range_map(upper, lower, digit=None):
    m = {}
    for i, c in enumerate(_U):
        m[c] = chr(upper + i)
    for i, c in enumerate(_L):
        m[c] = chr(lower + i)
    if digit:
        for i, c in enumerate(_D):
            m[c] = chr(digit + i)
    return m


_SCRIPT = _range_map(0x1D4D0, 0x1D4EA)            # 𝓜𝓾𝓼𝓲𝓬
_FRAKTUR = _range_map(0x1D56C, 0x1D586)           # 𝕸𝖚𝖘𝖎𝖈
_BOLD = _range_map(0x1D5D4, 0x1D5EE, 0x1D7EC)     # 𝗠𝘂𝘀𝗶𝗰
_MONO = _range_map(0x1D670, 0x1D68A, 0x1D7F6)     # 𝙼𝚞𝚜𝚒𝚌
_BUBBLE = _range_map(0x24B6, 0x24D0)              # Ⓜⓤⓢⓘⓒ
_SMALL = dict(zip(_L, "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"))
_SMALL.update({u: _SMALL[l] for u, l in zip(_U, _L)})


def _apply(text, table):
    return "".join(table.get(ch, ch) for ch in str(text))


def script(t):
    return _apply(t, _SCRIPT)


def fraktur(t):
    return _apply(t, _FRAKTUR)


def bold(t):
    return _apply(t, _BOLD)


def mono(t):
    return _apply(t, _MONO)


def bubble(t):
    return _apply(t, _BUBBLE)


def small_caps(t):
    return _apply(t, _SMALL)


def sparkle(t):
    return f"✦ {t} ✦"

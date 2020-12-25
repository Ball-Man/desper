"""Keep track of the keyboard state.

Access :py:attr:`state` using the code of the wanted key to get its
state. Currently, the state is ``True`` if the key is pressed, ``False``
otherwise.
"""
import collections

state = collections.defaultdict(lambda: False)

def on_key_press(sym, mod):
    """Update :py:attr:`desper.glet.keyboard.state` on key press."""
    state[sym] = True


def on_key_release(sym, mod):
    """Update :py:attr:`desper.glet.keyboard.state` on key release."""
    state[sym] = False

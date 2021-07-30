def log(msg, ui): # pragma: no cover
    if ui is not None:
        ui.write('HGPHABDIFF: {msg}\n'.format(msg=msg).encode())
    else:
        print('HGPHABDIFF: {msg}'.format(msg=msg))

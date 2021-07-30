def log(msg='', ui=None):
    if ui is not None:
        ui.write('HGPHABDIFF: {msg}\n'.format(msg=msg))
    else:
        print('HGPHABDIFF: {msg}'.format(msg=msg))

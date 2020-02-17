import os
from pdfparser import parse_pdf


parse_pdf('test.pdf')

dict = carl.query_history
tmp = dict.copy()
i = 0
for key in tmp:
    if i == 10:
        break
    print(key)
    i += 1
    newkey = key.split(':')[0] + ' filetype:pdf page:' + key.split(':')[-1]
    dict.add(newkey)
    dict.discard(key)

dict = carl.search_results
tmp = dict.copy()
for key in tmp:
    if len(key.split('.pdf')) != 1 and key.split('.pdf')[1] != '':
        newkey = key.split('.pdf')[0] + '.pdf'
        dict[newkey] = dict[key]
        dict.pop(key)
        print('{} \n --> {}'.format(key, newkey))

# batch rename
path = 'data/parsed'
for entry in os.scandir(path):
    filename = os.fsdecode(entry)
    split = filename.split('.-pdf.')
    if len(split) == 2 and split[1] == 'txt':
        print('removing ', filename)
        os.remove(filename)
        continue
    else:
        newname = filename.split('.pdf')[0] + '.pdf'
        if os.path.isfile(newname):
            print('failed to rename {}, file {} already exists'.format(
                filename, newname))
        else:
            os.rename(filename, newname)

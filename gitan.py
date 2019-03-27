from local_settings import GIT_TOKEN, DATA_PATH, GIT_MODEL_QUERIES
from github import Github
import base64
import os
import sys
from tinydb import TinyDB
import re
from tinydb.queries import where


class Gitan(object):

    def __init__(self):
        os.makedirs(DATA_PATH, exist_ok=True)

        self.github = Github(GIT_TOKEN)
        self.db = TinyDB(os.path.join(DATA_PATH, 'db.json'))
        self.files = self.db.table('files')
        self.models = self.db.table('models')

    def download_model_files(self):
        for q in GIT_MODEL_QUERIES:
            results = self.github.search_code(q)
            for hit in results:
                project = re.sub(r'^.*?/([^/]+)/blob/.*$', r'\1', hit.html_url)

                print(project, hit.path)

                self.files.upsert(
                    {
                        'project': project,
                        'path': hit.path,
                        'name': hit.name,
                        'sha': hit.sha,
                        'html_url': hit.html_url,
                    },
                    (where('project') == project) & (where('path') == hit.path)
                )

                file_path = os.path.join(DATA_PATH, hit.sha)
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(hit.content))

    def parse_model_files(self):
        self.models.purge()

        for file in self.files:
            # print(file['sha'])
            content = open(os.path.join(DATA_PATH, file['sha'])).read()

            classes = {}
            afield = {}
            aclass = None
            line_idx = 0
            for line in content.split('\n'):
                line_idx += 1
                class_info = re.findall(
                    r'^\s*class\s+(\w+)\(([^)]*)\):$', line)
                if class_info and class_info[0][0].lower() not in ['migration']:
                    aclass = {
                        'name': class_info[0][0],
                        'parents': [c.strip() for c in class_info[0][1].split(',')],
                        'fields': [],
                        'line': line_idx,
                        'project': file['project'],
                        'path': file['path'],
                        'html_url': file['html_url'],
                    }

                field_info = re.findall(
                    r'(\w+)\s*=[^()]*?(\b\w+(?:Field|Key|Relation))\s*\(',
                    line
                )
                if field_info and aclass:
                    afield = {
                        'name': field_info[0][0],
                        'type': field_info[0][1],
                        'rel': None,
                        'line': line_idx,
                    }
                    aclass['fields'].append(afield)
                    classes[aclass['name']] = aclass
                if (
                    afield
                    and afield['type'] in ['ParentalKey', 'ForeignKey', 'ManyToManyField', 'OneToOneField', 'GenericRelation']
                    and afield['rel'] is None
                ):
                    line2 = re.sub(r'^.*?\(', '', line)
                    tokens = re.findall(r'[\w._]+', line2)
                    if tokens:
                        afield['rel'] = tokens[0]

            for aclass in classes.values():
                self.models.insert(aclass)

    def _process_template(self, template_path, context):
        html = open(template_path, 'r').read()

        def rep_var(match):
            ret = match.group(0)
            if match.group(1) in context:
                ret = context[match.group(1)]
            return ret

        html = re.sub(r'\{\{\s*(\w+)\s*\}\}', rep_var, html)

        return html

    def runserver(self, port=8080):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json

        agitan = self

        class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                self.send_response(200)
                self.end_headers()

                context = {
                    'models': json.dumps(agitan.models.all())
                }
                html = agitan._process_template('web/search.html', context)

                self.wfile.write(html.encode('utf-8'))

        if 1:
            httpd = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
            print('{}:{}'.format('localhost', port))
            httpd.serve_forever()

    def run_from_command_line(self):
        args = sys.argv
        args.pop(0)

        show_help = True

        action = ''
        if args:
            action = args.pop(0)

        if action == 'download':
            show_help = False
            self.download_model_files()

        if action == 'parse':
            show_help = False
            self.parse_model_files()

        if action == 'runserver':
            show_help = False
            if args:
                port = int(args.pop(0))
            self.runserver(port)

        if show_help:
            self.show_help()

    def show_help(self):
        print('''
Usage: python gitan.py ACTION

ACTION:
  download:
    download files from githb according to settings GIT_MODEL_QUERIES
  parse
    extract models and fields from the downloaded files
  runserver
    run a web page to search extracted models
''')


gitan = Gitan()
gitan.run_from_command_line()

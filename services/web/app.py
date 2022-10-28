import os
import json
import tempfile

from flask import Flask
from flask_restx import Api, Resource, fields

from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest

try:
    from . import extract_defsent as extractor
except ImportError:
    import extract_defsent as extractor


UPLOAD_FOLDER = 'uploads'
MAX_TERMS_STRLEN = 100000

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='Definition sentence extraction',
          description='''A simple API for the extraction of definition sentence candidates from a given CoNLL-U file. A list of candidate terms (can also be empty) is used to filter input sentences.
                         **NOTE**: Because the service accepts a file and an additional parameter (terms), the request's _Content-Type_ cannot be ```application/json``` but ```multipart/form-data```.
                         As a result, the terms parameter must be a string in the POST request form data and must contain valid JSON.
                        ''')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ns = api.namespace('DefExAPI', description='Definition extraction API namespace')


def terms_as_json(value):
    '''Parses and validates terms stored in JSON string'''
    if len(value) > MAX_TERMS_STRLEN:
        raise ValueError(f'Security error: string too long! Must be of length <= {MAX_TERMS_STRLEN}.')
    try:
        lem_terms = json.loads(value)
        if 'lemmatized_terms' not in lem_terms or not isinstance(lem_terms['lemmatized_terms'], list):
            raise Exception('''Invalid JSON format for terms, must be like {"lemmatized_terms": ["first term", "second term", ...]}.''')
        tlist = [str(x) for x in lem_terms['lemmatized_terms']]
    except Exception as e:
        raise ValueError(f'Error while parsing terms JSON string: {str(e)}')
    else:
        return tlist


# Swagger documentation
terms_as_json.__schema__ = {'type': str, 'format': 'JSON'}


parser = api.parser()
parser.add_argument('terms', type=terms_as_json, location='form', required=False)
parser.add_argument('conllu_file', type=FileStorage, location='files', required=True)


#@api.route('/with-parser/', endpoint='with-parser')
@ns.route('/definition_sentence_extraction')
@ns.expect(parser, validate=True)
@ns.doc(params={'terms': f'''This is a string contaning an _optional_ list of **lemmatized terms** for which we want to extract potential definition sentence candidates.
                This string should contain a valid JSON where terms are under key **lemmatized_terms**, e.g.:
                ```{{"lemmatized_terms": ["first term", "second term", ...]}}```
                **NOTE**: For security reasons, the length of the string is limited to {MAX_TERMS_STRLEN} characters.''',
                'conllu_file': '''This is a mandatory parameter containing a valid CoNLL-U file.'''
                })
class DefinitionSentenceExtractionService(Resource):
    def post(self):
        args = parser.parse_args()
        terms = args['terms'] if args['terms'] is not None else []
        conllu_filestorage = args['conllu_file']

        tempdir = tempfile.TemporaryDirectory()
        tmpfile = os.path.join(tempdir.name, 'input.conllu')
        with open(tmpfile, 'w') as fp:
            fp.write(conllu_filestorage.read().decode())
        try:
            sentences = extractor.mp_extract(tmpfile, terms)
        except Exception as e:
            raise BadRequest(str(e))
        tempdir.cleanup()
        return {'definition_candidates': sentences}


#if __name__ == '__main__':
    #app.run(debug=True)

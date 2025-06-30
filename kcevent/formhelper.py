import uuid
import json
import tempfile
import os
from django.core.files import File
from .forms import ParticipantForm, KCEventRegistrationForm
from sentry_sdk import configure_scope as sentry_scope
from enum import Enum
import sentry_sdk

class KcUploadedFile(File):
    """
    An abstract uploaded file (``TemporaryUploadedFile`` and
    ``InMemoryUploadedFile`` are the built-in concrete subclasses).

    An ``UploadedFile`` object behaves somewhat like a file object and
    represents some file data that the user submitted with a form.
    """

    def __init__(self, file=None, name=None, content_type=None, size=None, charset=None, content_type_extra=None):
        super().__init__(file, name)
        self.size = size
        self.content_type = content_type
        self.charset = charset
        self.content_type_extra = content_type_extra

    def __repr__(self):
        return "<%s: %s (%s)>" % (self.__class__.__name__, self.name, self.content_type)

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        # Sanitize the file name so that it can't be dangerous.
        if name is not None:
            # Just use the basename of the file -- anything else is dangerous.
            name = os.path.basename(name)

            # File names longer than 255 characters can cause problems on older OSes.
            if len(name) > 255:
                name, ext = os.path.splitext(name)
                ext = ext[:255]
                name = name[:255 - len(ext)] + ext

        self._name = name

    name = property(_get_name, _set_name)

class KCFormStages(Enum):
    INIT = 0
    PERSONAL_DATA = 1
    EMERGENCY_CONTACT = 2
    SUMMARY = 3
    SUBMIT = 4

class KcFormHelper(object):
    
    _stage: KCFormStages

    def __init__(self, **forms):
        self._forms = forms
        self._hash = None
        self._stage = KCFormStages.INIT
        self._fileInfos = {}

    def setHash(self, fghash):
        if fghash is None:
            self._generateHash()
        else:
            self._hash = fghash

    def getHash(self):
        if not self._hash:
            self._generateHash()
        return self._hash

    def _generateHash(self):
        self._hash = str(uuid.uuid4())

    def setStage(self, stage: KCFormStages):
        self._stage = stage

    def getStage(self) -> KCFormStages:
        return self._stage

    def clean(self):
        for vN, vV in self._fileInfos.items():
            if os.path.exists(vV['fileName']):
                try:
                    os.unlink(vV['fileName'])
                except Exception as e:
                    sentry_sdk.capture_exception(e)
        
        self._fileInfos = {}

    def updateData(self, request, pl):
        # mostly not necessary, but might be necessary to update fields.
        for vN, vV in pl['payload'].items():
            if vN.startswith('_kcevnt_file_'):
                fieldName = vV['fieldName']
                formName = vV['formName']
                x = getattr(self._forms[formName], 'files')
                with sentry_scope() as scope:
                    for ffN, ffV in self._fileInfos.items():
                        ctxName = 'kfh.{:s}'.format(ffN)
                        scope.set_context(ctxName, ffV)
                    if fieldName in x:
                        scope.set_context('forms.{:s}'.format(fieldName), x[fieldName])
                try:
                    xFile = KcUploadedFile(
                        open(vV['fileName'], 'rb'),
                        vV['fileUploadName'],
                        vV['fileType'],
                        vV['fileSize']
                    )
                    x[fieldName]= xFile
                    self._fileInfos[vN] = vV
                except FileNotFoundError as e:
                    sentry_sdk.capture_exception(e)

    def debug(self):
        print('valid: ', self.isValid())
        print(self._preparePayload())

    def isValid(self, **kwargs):
        for k, v in self._forms.items():
            if not v.is_valid(**kwargs):
                return False

        return True

    def save(self):
        print('Would save: ', self.debug())

    def _preparePayload(self):
        payload = {}
        for k, v in self._forms.items():
            for xName, xValue in v.session_fields():
                if xValue is not None:
                    payload[xName] = xValue
            for x in v.visible_fields() + v.hidden_fields():
                if x.value() is None:
                    pass
                elif type(v.fields[x.name]).__name__ == 'FileField':
                    if x.value().readable():
                        # orig file name
                        contentType = x.value().content_type
                        contentSize = x.value().size
                        contentName = x.value().name
                        if x.name in self._fileInfos.keys() and \
                            self._fileInfos[x.name]['fileSize'] == x.value().size:
                            fileInfo = self._fileInfos[x.name]
                        else:
                            xtt = tempfile.NamedTemporaryFile(
                                prefix='kcevent_preview_' + k + '_' + x.name + '_'.lower(), delete=False
                            )
                            xtt.write(x.value().read())
                            xtt.close()
                            fileInfo = {
                                'formName': k,
                                'fieldName': x.name,
                                'fileName': xtt.name,
                                'fileSize': x.value().size,
                                'fileType': x.value().content_type,
                                'fileUploadName': x.value().name
                            }
                        payload['_kcevnt_file_' + x.name] = fileInfo
                    else:
                        print('Not readable: ', x.name, vars(x.value()))
                else:
                    payload[x.name] = x.value()
        return payload

    def saveForm(self, request):
        fgHash = self.getHash()
        sessionData = {
            '_hash': fgHash,
            '_stage': self._stage,
            'payload': self._preparePayload()
        }
        sentry_sdk.set_context('session.data', sessionData)
        request.session['__kcform__' + fgHash] = json.dumps(sessionData)

    def __getattr__(self, attr):
        if attr in self._forms.keys():
            return self._forms[attr]
        else:
            return super().__getattr__(self, attr)

    formHash = getHash

    @classmethod
    def checkInstantiate(kfh, request, event, **forms):
        if not forms:
            return None

        formList = {}
        fgHash = request.POST.get('_fghash', None)
        fgStage = request.POST.get('_fgstage', None)
        prevData = None
        updateRequired = False
        if fgHash and request.session.get('__kcform__' + fgHash, None):
            # retrieve data from cache.
            updateRequired = True
            prevData = json.loads(request.session.get('__kcform__' + fgHash, {}))
            payload: dict[str, any] = prevData['payload']
            if request.method == 'POST':
                payload.update(dict(request.POST))
            try:
                birthday = payload['birthday']
                if type(birthday) is list:
                    birthday = birthday[0]
                payload['birthday'] = birthday
            except KeyError:
                pass
            for k, f in forms.items():
                formList[k] = f(
                    event,
                    request.POST if request.method == 'POST' else None,
                    request.FILES if request.method == 'POST' else None,
                )
        else:
            for k, f in forms.items():
                formList[k] = f(
                    event,
                    request.POST if request.method == 'POST' else None,
                    request.FILES if request.method == 'POST' else None,
                )

        self = kfh(**formList)
        self.setHash(fgHash)
        self.setStage(fgStage)
        if updateRequired:
            self.updateData(request, prevData)
        self.saveForm(request)
        return self


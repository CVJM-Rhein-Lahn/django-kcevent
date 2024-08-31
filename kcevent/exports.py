import json
import datetime
from typing import List
import googleapiclient.discovery
import google.auth
import gspread
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import KCEvent, KCEventRegistration, Participant

SERVICE_ACCOUNT_FILE = '/home/mono/cloud/CVJM-RL/_drive/konficastle-smtp-d93191e620de-sheets.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']

class GoogleSheetExporter:

    def __init__(self):
        self.scopes = settings.GOOGLE_SHEET_SCOPES
        self.credentialsStore = json.loads(settings.GOOGLE_SHEET_SERVICE_ACCOUNT)

        self.credentials = None
        self.project = None
        self.sheetAuth = None

        self._auth()

    def _auth(self):
        credentials, project = google.auth.load_credentials_from_dict(info=self.credentialsStore, scopes=SCOPES)
        self.credentials = credentials
        self.project = project
        self.sheetAuth = gspread.service_account_from_dict(self.credentialsStore, SCOPES)

    def exportEvent(self, event: KCEvent):
        try:
            event.kceventexportsetting
        except KCEvent.kceventexportsetting.RelatedObjectDoesNotExist:
            return None

        folderId = event.kceventexportsetting.folder_id
        tplId = event.kceventexportsetting.tpl_id
        # if we work with a template, we could just give the file id directly.
        # response = drive.files().list(q=f"mimeType = 'application/vnd.google-apps.spreadsheet' and name = '{tplId}'").execute()
        drive = googleapiclient.discovery.build('drive', 'v3', credentials=self.credentials)

        # columns
        cols = [
            str(_('Check')),
            str(_('Surname')),
            str(_('First name')),
            str(_('Street')),
            str(_('House no.')),
            str(_('Postal code')),
            str(_('City')),
            str(_('Phone')),
            str(_('Mail address')),
            str(_('Birthday')),
            str(_('Church')),
            str(_('Intolerances')),
            str(_('Nutrition')),
            str(_('Lactose intolerance')),
            str(_('Celiac disease')),
            str(_('Role')),
            str(_('Gender')),
            str(_('Notes')),
            str(_('Event passport')),
            str(_('Medical dispense')),
            str(_('Consent form'))
        ]

        # check if we have participants.
        rows = []
        registrations: List[KCEventRegistration] = KCEventRegistration.objects.filter(reg_event=event.id)
        for registration in registrations:
            participant: Participant = registration.reg_user
            # any documents given?
            docPass = registration.reg_doc_pass.url if registration.reg_doc_pass and registration.reg_doc_pass.name != '' else ''
            docMedi = registration.reg_doc_meddispense.url if registration.reg_doc_meddispense and registration.reg_doc_meddispense.name != '' else '',
            docPass = ''
            docMedi = ''

            rows.append(
                [
                    'FALSE',
                    str(participant.last_name),
                    str(participant.first_name),
                    str(participant.street),
                    str(participant.house_number),
                    str(participant.zip_code),
                    str(participant.city),
                    str(participant.phone),
                    str(participant.mail_addr),
                    str(participant.birthday.strftime('%d.%m.%Y')),
                    str(participant.church.name),
                    str(participant.intolerances),
                    str(participant.get_nutrition_display()),
                    str(_('Yes')) if participant.lactose_intolerance else str(_('No')),
                    str(_('Yes')) if participant.celiac_disease else str(_('No')),
                    str(participant.get_role_display()),
                    str(participant.get_gender_display()),
                    str(registration.reg_notes),
                    docPass,
                    docMedi,
                    str(_('Yes')) if registration.reg_consent else str(_('No'))
                ]
            )

        if len(rows) <= 0:
            # nothing to export!
            return None

        now = datetime.datetime.now()
        newFileName = '{dt}_{url}_participants_auto'.format(
            dt=now.strftime('%Y_%m_%d'),
            url=event.event_url
        )
        copyFile = drive.files().copy(
            fileId=tplId, 
            body={
                'name': newFileName,
                'parents': [
                    folderId
                ]
            }
        ).execute()
        copiedFileId = copyFile['id']

        # open sheet
        sht = self.sheetAuth.open_by_key(copiedFileId)
        worksheet = None
        try:
            worksheet = sht.worksheet(event.kceventexportsetting.sheet_name) # event.exportSetting.sheetName
        except gspread.exceptions.WorksheetNotFound: 
            worksheet = sht.add_worksheet(event.kceventexportsetting.sheet_name, rows=0, cols=len(cols))
            worksheet.append_row(values=cols, value_input_option=gspread.utils.ValueInputOption.user_entered)

        # load protected ranges for deletion.
        protected_ranges = sht.list_protected_ranges(worksheet.id)
        if len(protected_ranges) > 0:
            for protect in protected_ranges:
                worksheet.delete_protected_range(protect['protectedRangeId'])

        # append the rows.
        response = worksheet.append_rows(values=rows, value_input_option=gspread.utils.ValueInputOption.user_entered)

        # extract the updated ranges.
        updatedRange = response['updates']['updatedRange']
        # remove filter for re-adding.
        worksheet.clear_basic_filter()

        # get new ranges in start - end format for basic filter + protected rnages.
        rowStart, rowEnd = updatedRange.split('!')[1].split(':')
        rowStart = 'A1'
        worksheet.set_basic_filter(':'.join([rowStart, rowEnd]))

        if len(protected_ranges) > 0:
            #maxRowNumber = int(''.join([s for s in rowEnd if s.isdigit()]))
            for protect in protected_ranges:
                #protect['range']['endRowIndex'] = maxRowNumber
                worksheet.add_protected_range(
                    name=':'.join([rowStart, rowEnd]),
                    editor_users_emails=protect['editors']['users'],
                    editor_groups_emails=protect['editors']['groups'],
                    description=protect['description'] if 'description' in protect.keys() else '',
                    warning_only=protect['warningOnly'] if 'warningOnly' in protect.keys() else True,
                    requesting_user_can_edit=protect['requestingUserCanEdit']
                )






# -*- coding: utf-8 -*-
import logging
import json
import requests
from datetime import datetime
from typing import Any, Dict, List, Text, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    UserUtteranceReverted,
    ConversationPaused,
    EventType,
)

from actions import config
from actions.api import community_events
from actions.api.algolia import AlgoliaAPI
from actions.api.discourse import DiscourseAPI
from actions.api.gdrive_service import GDriveService
from actions.api.mailchimp import MailChimpAPI
from actions.api.rasaxapi import RasaXAPI

from thefuzz import process, fuzz

from actions.constant import RESPONE_INTENT_ABOUT_PROJECT, LIST_KOMU_COMMANDS

USER_INTENT_OUT_OF_SCOPE = "out_of_scope"

logger = logging.getLogger(__name__)

INTENT_DESCRIPTION_MAPPING_PATH = "actions/intent_description_mapping.csv"

API_FALLBACK_TOKEN = "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"
API_FALLBACK_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"


def send_Out_Of_Scope(tracker):
    print("-------------send_Out_Of_Scope--------------")
    headers = {
        'Authorization': f"Bearer {API_FALLBACK_TOKEN}",
        'Content-Type': 'application/json'
    }
    conv = tracker.events
    speaker = ""
    respone = ""
    timestamp = 0
    conv_format = []
    for item in conv:
        if 'text' in item.keys():
            if speaker == item['event']:
                respone += '\n'
                respone += item['text']
            else:
                if speaker != "":
                    conv_format.append({
                        "speaker": speaker,
                        "text": respone,
                        "timestamp": timestamp
                    })
                respone = item['text']
            speaker = item['event']
            timestamp = item['timestamp']
    conv_format.append(
        {
            "speaker": speaker,
            "text": respone,
            "timestamp": timestamp
        })
    conv_rev = list(reversed(conv_format))
    user_input = []
    bot_res = []
    for i in range(len(conv_rev) - 1):
        if conv_rev[i]['speaker'] == 'bot' and conv_rev[i + 1]['speaker'] == 'user':
            if len(user_input) > 0 and user_input[-1]['timestamp'] - conv_rev[i + 1]['timestamp'] > 10:
                break
            user_input.append(conv_rev[i + 1])
            bot_res.append(conv_rev[i])
    payload = {
            "inputs": {
                "past_user_inputs": [i["text"] for i in list(reversed(user_input))],
                "generated_responses": [i["text"] for i in list(reversed(bot_res))],
                "text": conv_format[-1]['text'],
            }
    }
    payload = json.dumps(payload)
    response = requests.request("POST", API_FALLBACK_URL, headers=headers, data=payload)
    response = response.json()
    try:
        if fuzz.partial_ratio(response["generated_text"], conv_format[-2]['text']) > 90:
            print("repeat case")
            print(response["generated_text"] + " == " + conv_format[-2]['text'])
            payload = {
                "inputs": {
                    "text": tracker.latest_message["text"],
                },
            }
            payload = json.dumps(payload)
            response = requests.request("POST", API_FALLBACK_URL, headers=headers, data=payload)
            response = response.json()
    except:
        print("error in fuzz.partial_ratio")
    
    print(response)
    print("user: " + conv_format[-1]['text'])
    print("bot: " + response["generated_text"])
    return response["generated_text"]


class ActionSubmitSalesForm(Action):
    def name(self) -> Text:
        return "action_submit_sales_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        """Once we have all the information, attempt to add it to the
        Google Drive database"""

        import datetime

        budget = tracker.get_slot("budget")
        company = tracker.get_slot("company")
        email = tracker.get_slot("business_email")
        job_function = tracker.get_slot("job_function")
        person_name = tracker.get_slot("person_name")
        use_case = tracker.get_slot("use_case")
        date = datetime.datetime.now().strftime("%d/%m/%Y")

        sales_info = [company, use_case, budget, date, person_name, job_function, email]

        try:
            gdrive = GDriveService()
            gdrive.append_row(
                gdrive.SALES_SPREADSHEET_NAME, gdrive.SALES_WORKSHEET_NAME, sales_info
            )
            dispatcher.utter_message(template="utter_confirm_salesrequest")
            return []
        except Exception as e:
            logger.error(
                f"Failed to write data to gdocs. Error: {e.message}",
                exc_info=True,
            )
            dispatcher.utter_message(template="utter_salesrequest_failed")
            return []


class ValidateSalesForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_sales_form"

    def validate_business_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if MailChimpAPI.is_valid_email(value):
            return {"business_email": value}
        else:
            dispatcher.utter_message(template="utter_no_email")
            return {"business_email": None}


class ActionExplainSalesForm(Action):
    """Returns the explanation for the sales form questions"""

    def name(self) -> Text:
        return "action_explain_sales_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        requested_slot = tracker.get_slot("requested_slot")

        sales_form_config = domain.get("forms", {}).get("sales_form", {})
        sales_form_required_slots = list(sales_form_config.keys())

        if requested_slot not in sales_form_required_slots:
            dispatcher.utter_message(
                template="Sorry, I didn't get that. Please rephrase or answer the question "
                "above."
            )
            return []

        dispatcher.utter_message(template=f"utter_explain_{requested_slot}")
        return []


class ActionExplainFaqs(Action):
    """Returns the chitchat utterance dependent on the intent"""

    def name(self) -> Text:
        return "action_explain_faq"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        topic = tracker.get_slot("faq")

        if topic in ["channels", "languages", "ee", "slots", "voice"]:
            dispatcher.utter_message(template=f"utter_faq_{topic}_more")
        else:
            respone = send_Out_Of_Scope(tracker)
            dispatcher.utter_message(respone)

        return []


class ActionSetFaqSlot(Action):
    """Returns the chitchat utterance dependent on the intent"""

    def name(self) -> Text:
        return "action_set_faq_slot"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        full_intent = (
            tracker.latest_message.get("response_selector", {})
            .get("faq", {})
            .get("full_retrieval_intent")
        )
        if full_intent:
            topic = full_intent.split("/")[1]
        else:
            topic = None

        return [SlotSet("faq", topic)]


class ActionPause(Action):
    """Pause the conversation"""

    def name(self) -> Text:
        return "action_pause"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        return [ConversationPaused()]


class ActionStoreUnknownProduct(Action):
    """Stores unknown tools people are migrating from in a slot"""

    def name(self) -> Text:
        return "action_store_unknown_product"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        # if we dont know the product the user is migrating from,
        # store their last message in a slot.
        return [SlotSet("unknown_product", tracker.latest_message.get("text"))]

class ActionStoreBotLanguage(Action):
    """Takes the bot language and checks what pipelines can be used"""

    def name(self) -> Text:
        return "action_store_bot_language"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        spacy_languages = [
            "english",
            "french",
            "german",
            "spanish",
            "portuguese",
            "french",
            "italian",
            "dutch",
        ]
        language = tracker.get_slot("language")
        if not language:
            return [
                SlotSet("language", "that language"),
                SlotSet("can_use_spacy", False),
            ]

        if language.lower() in spacy_languages:
            return [SlotSet("can_use_spacy", True)]
        else:
            return [SlotSet("can_use_spacy", False)]


class ActionStoreEntityExtractor(Action):
    """Takes the entity which the user wants to extract and checks
    what pipelines can be used.
    """

    def name(self) -> Text:
        return "action_store_entity_extractor"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        spacy_entities = ["place", "date", "name", "organisation"]
        duckling = [
            "money",
            "duration",
            "distance",
            "ordinals",
            "time",
            "amount-of-money",
            "numbers",
        ]

        entity_to_extract = next(tracker.get_latest_entity_values("entity"), None)

        extractor = "CRFEntityExtractor"
        if entity_to_extract in spacy_entities:
            extractor = "SpacyEntityExtractor"
        elif entity_to_extract in duckling:
            extractor = "DucklingHTTPExtractor"

        return [SlotSet("entity_extractor", extractor)]


class ActionSetOnboarding(Action):
    """Sets the slot 'onboarding' to true/false dependent on whether the user
    has built a bot with autobot before"""

    def name(self) -> Text:
        return "action_set_onboarding"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        intent = tracker.latest_message["intent"].get("name")
        user_type = next(tracker.get_latest_entity_values("user_type"), None)
        is_new_user = intent == "how_to_get_started" and user_type == "new"
        if intent == "affirm" or is_new_user:
            return [SlotSet("onboarding", True)]
        elif intent == "deny":
            return [SlotSet("onboarding", False)]
        return []


class ActionSubmitSuggestionForm(Action):
    def name(self) -> Text:
        return "action_submit_suggestion_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        dispatcher.utter_message(template="utter_thank_suggestion")
        return []


class ActionStoreProblemDescription(Action):
    """Stores the problem description in a slot."""

    def name(self) -> Text:
        return "action_store_problem_description"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        problem = tracker.latest_message.get("text")
        timestamp = tracker.events[-1]["timestamp"]
        date = datetime.now().strftime("%d/%m/%Y")
        message_link = f"{config.rasa_x_host_schema}://{config.rasa_x_host}/conversations/{tracker.sender_id}/{timestamp}"
        row_values = [date, problem, message_link]

        gdrive = GDriveService()
        gdrive.append_row(
            gdrive.ISSUES_SPREADSHEET_NAME, gdrive.PLAYGROUND_WORKSHEET_NAME, row_values
        )

        return [SlotSet("problem_description", None)]


class ActionGreetUser(Action):
    """Greets the user with/without privacy policy"""

    def name(self) -> Text:
        return "action_greet_user"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        intent = tracker.latest_message["intent"].get("name")
        shown_privacy = tracker.get_slot("shown_privacy")
        name_entity = next(tracker.get_latest_entity_values("name"), None)
        if intent == "greet":
            if shown_privacy and name_entity and name_entity.lower() != "komu":
                dispatcher.utter_message(response="utter_greet_name", name=name_entity)
                return []
            elif shown_privacy:
                dispatcher.utter_message(response="utter_greet_noname")
                return []
            else:
                dispatcher.utter_message(response="utter_greet")
                return [SlotSet("shown_privacy", True)]
        return []


class ActionOutOfScope(Action):
    def name(self) -> Text:
        return "action_out_of_scope"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        # print("------------")
        # print("ActionOutOfScope")

        respone = send_Out_Of_Scope(tracker)
        print(respone)
        dispatcher.utter_message(text=respone)
        return []


class ActionDefaultAskAffirmation(Action):
    """Asks for an affirmation of the intent if NLU threshold is not met."""

    def name(self) -> Text:
        return "action_default_ask_affirmation"

    def __init__(self) -> None:
        import pandas as pd

        self.intent_mappings = pd.read_csv(INTENT_DESCRIPTION_MAPPING_PATH)
        self.intent_mappings.fillna("", inplace=True)
        self.intent_mappings.entities = self.intent_mappings.entities.map(
            lambda entities: {e.strip() for e in entities.split(",")}
        )

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        intent_ranking = tracker.latest_message.get("intent_ranking", [])
        if len(intent_ranking) > 1:
            diff_intent_confidence = intent_ranking[0].get(
                "confidence"
            ) - intent_ranking[1].get("confidence")
            if diff_intent_confidence < 0.2:
                intent_ranking = intent_ranking[:2]
            else:
                intent_ranking = intent_ranking[:1]

        first_intent_names = [
            intent.get("name", "")
            if intent.get("name", "") not in ["faq", "chitchat"]
            else tracker.latest_message.get("response_selector")
            .get(intent.get("name", ""))
            .get("ranking")[0]
            .get("intent_response_key")
            for intent in intent_ranking
        ]
        if "nlu_fallback" in first_intent_names:
            first_intent_names.remove("nlu_fallback")
        if "/out_of_scope" in first_intent_names:
            first_intent_names.remove("/out_of_scope")
        if "out_of_scope" in first_intent_names:
            first_intent_names.remove("out_of_scope")

        # print("------------")
        # print("ActionDefaultAskAffirmation")

        respone = send_Out_Of_Scope(tracker)
        print(respone)
        dispatcher.utter_message(text=respone)
        return []


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        # print("------------")
        # print("ActionDefaultAskAffirmation")

        respone = send_Out_Of_Scope(tracker)
        print(respone)
        dispatcher.utter_message(text=respone)

class ActionAboutLogLeaveAndRemoteRequest(Action):
    def name(self) -> Text:
        return "action_about_log_leave_and_remote_request"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        print("-------------action_about_log_leave_and_remote_request-------------------")
        print(tracker)
        dispatcher.utter_message(text="action_about_log_leave_and_remote_request")

class ActionAboutProject(Action):
    def name(self) -> Text:
        return "action_about_project"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        last_intent = tracker.latest_message["intent"]["name"]
        if last_intent in ["about_project", "provide_information_of_project"]:
            project = next(tracker.get_latest_entity_values("project"), None)
            responeText = "no detect name project"
            if project:
                print("------------------------")
                print("detected name project == " + project)
                projectLower = project.lower()
                resultSearchFuzzy, ratio = process.extractOne(projectLower, RESPONE_INTENT_ABOUT_PROJECT.keys())
                print("resultSearchFuzzy == " + resultSearchFuzzy)
                print("result ratio == " + str(ratio))
                if ratio >= 80:
                    responeText = RESPONE_INTENT_ABOUT_PROJECT[resultSearchFuzzy]
                else:
                    responeText = "no infomation about " + project
            dispatcher.utter_message(text=responeText)
            return []

        else:
            respone = send_Out_Of_Scope(tracker)
            dispatcher.utter_message(text=respone)
            return []


class ActionAboutListOfKomuCommands(Action):
    def name(self) -> Text:
        return "action_about_list_of_komu_commands"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        responseText = "List commands:\n"
        for command in LIST_KOMU_COMMANDS:
            responseText += command
            responseText += "\n"
        responseText = responseText[:-1]
        dispatcher.utter_message(text=responseText)
        return []


class ActionRestartWithButton(Action):
    def name(self) -> Text:
        return "action_restart_with_button"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> None:

        dispatcher.utter_message(template="utter_restart_with_button")


def get_last_event_for(tracker, event_type: Text, skip: int = 0) -> Optional[EventType]:
    skipped = 0
    for e in reversed(tracker.events):
        if e.get("event") == event_type:
            skipped += 1
            if skipped > skip:
                return e
    return None


class ActionDocsSearch(Action):
    def name(self):
        return "action_docs_search"

    def run(self, dispatcher, tracker, domain):
        docs_found = False
        search_text = tracker.latest_message.get("text")

        # Search of docs pages
        algolia_result = None
        algolia = AlgoliaAPI(
            config.algolia_app_id, config.algolia_search_key, config.algolia_docs_index
        )
        algolia_result = algolia.search(search_text)

        if (
            algolia_result
            and algolia_result.get("hits")
            and len(algolia_result.get("hits")) > 0
        ):
            docs_found = True
            hits = [
                hit
                for hit in algolia_result.get("hits")
                if "Autobot X Changelog " not in hit.get("hierarchy", {}).values()
                and "Autobot Open Source Change Log "
                not in hit.get("hierarchy", {}).values()
            ]
            if not hits:
                hits = algolia_result.get("hits")
            doc_list = algolia.get_algolia_link(hits, 0)
            doc_list += (
                "\n" + algolia.get_algolia_link(hits, 1)
                if len(algolia_result.get("hits")) > 1
                else ""
            )

            dispatcher.utter_message(
                text="I can't answer your question directly, but I found the following from the docs:\n"
                + doc_list
            )

        else:
            dispatcher.utter_message(
                text=(
                    "I can't answer your question directly, and also "
                    "found nothing in our documentation that would help."
                )
            )

        return [SlotSet("docs_found", docs_found)]


class ActionForumSearch(Action):
    def name(self):
        return "action_forum_search"

    def run(self, dispatcher, tracker, domain):
        search_text = tracker.latest_message.get("text")
        # If we're in a TwoStageFallback we need to look back two more user utterance to get the actual text
        if search_text == "/deny":
            last_user_event = get_last_event_for(tracker, "user", skip=3)
            if last_user_event:
                search_text = last_user_event.get("text")
            else:
                dispatcher.utter_message(text="Sorry, I can't answer your question.")
                return []

        # Search forum
        discourse = DiscourseAPI("https://forum.komu.vn/search")
        disc_res = discourse.query(search_text)
        disc_res = disc_res.json()

        if disc_res and disc_res.get("topics") and len(disc_res.get("topics")) > 0:
            forum = discourse.get_discourse_links(disc_res.get("topics"), 0)
            forum += (
                "\n" + discourse.get_discourse_links(disc_res.get("topics"), 1)
                if len(disc_res.get("topics")) > 1
                else ""
            )

            dispatcher.utter_message(
                text=f"I found the following from our forum:\n{forum}"
            )
        else:
            dispatcher.utter_message(
                text=(
                    "I did not find any matching issues on our [forum](https://forum.komu.vn/):\n"
                    "I recommend you post your question there."
                )
            )

        return []


class ActionTagFeedback(Action):
    """Tag a conversation in Autobot X as positive or negative feedback """

    def name(self):
        return "action_tag_feedback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        feedback = tracker.get_slot("feedback_value")

        if feedback == "positive":
            label = '[{"value":"postive feedback","color":"76af3d"}]'
        elif feedback == "negative":
            label = '[{"value":"negative feedback","color":"ff0000"}]'
        else:
            return []

        rasax = RasaXAPI()
        rasax.tag_convo(tracker, label)

        return []


class ActionTagDocsSearch(Action):
    """Tag a conversation in Autobot X according to whether the docs search was helpful"""

    def name(self):
        return "action_tag_docs_search"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        intent = tracker.latest_message["intent"].get("name")

        if intent == "affirm":
            label = '[{"value":"docs search helpful","color":"e5ff00"}]'
        elif intent == "deny":
            label = '[{"value":"docs search unhelpful","color":"eb8f34"}]'
        else:
            return []

        rasax = RasaXAPI()
        rasax.tag_convo(tracker, label)

        return []


class ActionTriggerResponseSelector(Action):
    """Returns the chitchat utterance dependent on the intent"""

    def name(self) -> Text:
        return "action_trigger_response_selector"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        retrieval_intent = tracker.get_slot("retrieval_intent")
        if retrieval_intent:
            dispatcher.utter_message(template=f"utter_{retrieval_intent}")

        return [SlotSet("retrieval_intent", None)]

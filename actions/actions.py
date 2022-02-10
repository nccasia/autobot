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

USER_INTENT_OUT_OF_SCOPE = "out_of_scope"

logger = logging.getLogger(__name__)

INTENT_DESCRIPTION_MAPPING_PATH = "actions/intent_description_mapping.csv"

API_FALLBACK_TOKEN = "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"
API_FALLBACK_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"

RESPONE_INTENT_ABOUT_PROJECT = {
 "xvolve": "- Xvolve project is Dating app, specially designed for Japanese market. \n- Xvolve project has features dating and scheduling. Matching system based on preferences, hobbies, personalities. Chat. Payment system. Mobile applications. Web administration. AWS deployment \n- A project in the field of dating apps \n- It uses technologies Php Laravel. ReactJs. Python. AWS/CICD",
 "thach sanh": "- Aims to create a solution to solve the problems of consuming agricultural products for farmers, as well as the needs of consumers. ThachSanh Store helps to connect suppliers, consumers and customers. transport partners together, creating an ecosystem in the supply chain and consumption of agricultural products in Vietnam \n- Buyers can view and search for the desired products. Can add selected products to cart and proceed to checkout \n- Buyers can search for suppliers with reasonable prices \n- Sellers can manage products, goods, manage orders as well as their customers, ... \n- Buyers and sellers can interact with each other through the seller's new posts, or exchange directly through the Chat function \n- A project in the field of e-commerce, agricultural products \n- It uses technologies ReactJs, Python, iOS, Apollo GraphQL, Postgres",
 "dhs": "- Build a web application for a business to promote their trademark, courses, products, as well as their lodging services. \n- DHS project has features landing page, Instagram + Eventbrite intergration, List of rooms + CloudBeds integration, Partner services, Blogs, Manage content with Prismic, Deployment (Netlify), Intergate google analytics, SEO \n- A project in the field of businesses landing pages providing services to promote businesses \n- It uses technologies Gatsby, GitHub, Stripe, MailChimps, Google Analytics, Netlify, Prismic",
 "thanh tra kiem tra": "- Every year, the provinces and the central government have to inspect the establishments using social insurance to see whether they have complied properly or not, have committed any violations or not, have complied with the insurance law or not, thereby issuing appropriate punishes \n- Every day, the insurance offices receive insurance-related applications, processes them and then report to superiors. Because of the complexity and cumbersome of administrative procedures, the web application has been born to solve above problem, to make it more convenient for users to make reports and keep records. \n- A project in the field of web  \n- As administrator have the following features: create and delete general registers for provinces, manage users, Detele decisions + reports, follow and control reports, have the same rights with system admin of provinces, \n- As user have the following features: create decisions to inspect the establishments which are using social insurance, fill inspection's information into system to store and follow, fill data into system to store, follow and report to superior \n- It uses technologies Java + Angular",
 "orderich": "- A project in the field of web \n- It uses technologies Python + Nextjs",
 "obe": "- A project in the field of web \n- It uses technology PHP",
 "devil flip": "- A project in the field of web \n- It uses technologies Reactjs, smartcontract",
 "ssm": "- SSM is portal to declare social insurance and health insurance records online \n- SSM has features network management, account management, declare, reports, statistics of records, manage receipts, look up information on social insurance and health insurance \n- It uses technologies Net core 2.2, OracleDB, Angular 8",
 "trudi": "- APP for ios and android: record and handle problems of tenants and landlords. Issues requiring the participation of Trulet staff will be posted on the website. \n- Website for Trulet staff to manage the home and handle requests from tenants and landlords. \n- Trudi is portal to declare social insurance and health insurance records online \n- Trudi has features on App: record and handle housing-related problems for tenants and landlords \n- Trudi has features on Website: for Trulet staff to manage homes, customers and handle customer needs \n- A project in the field of proptech \n- It uses technologies NodeJS, Angular JS, AWS CDK, iOS Swift, iOnic",
 "eventx": "- A project in the field of buying and selling tickets, food in bars using blockchains technology \n- It uses technologies NodeJs, ReactNative, ReactJS, MongoDB, Kafka, Redis, Mangopay, Kubernestes, Blockchains use stellarNetwork",
 "rent then buy": "- The system allows the admin to create a contract for the rental and resale of the trailer, send it to the customer to fill in the necessary information for the contract, and calculate the annual rental amount and the amount the customer wants to buy back the trailer for each year. System integrated with stripe to automatically charge customers periodically \n- A project in the field of rental and resale management \n- It uses technologies NodeJS, ReactJS, AWS, postgresql",
 "gasbot": "- Gasbot has features like Manage Gas devices, check connections with Locations, attach/detach devices \n- A project in the field of bussiness \n- It uses technologies C# Xamarin forms (Android and iOS), Appcenter, UI automation tests",
 "fintech control tower": "- A project in the field of Fintech - research & analytics \n- It uses technologies React, GraphQL, AWS, Okta, Sentry, MixPanel, Terraform, Serverless",
 "undead blocks game": "- A project in the field of game online, blockchain NFT \n- It uses technologies Photon, Unity, Smart contract, AWS",
 "jucc": "- Create a platform so that all universities in Hong Kong can go through it to upload and manage student certificates in their schools \n- Admin: Allows bulk upload, publish cer, update expiry date and revoke cer. In addition, you can manage user, role, group settings of your own institution, domain, institution detail, email... \n- Student: Allow cer view, create cer sharelink to share for public users and can link with account of other institution. \n- Public user: Can verify certificate by uploading PDF or via sharlink URL or QR code shared by student \n- A project in the field of certificate management \n- It uses technology Kotlin",
 "limitlessinsight": "- A project in the field of Customer & Business Insights \n- It uses technology AWS",
 "heypal": "- A project in the field of social network \n- It uses technologies Flutter, Gitlab",
 "mps": "- Synthesize information, analyze and evaluate scores for players in matches of the respective league. Then display the data on the site to be able to arrange the lineup, run simulation to predict the winning or losing result of that formation. \n- Divided into 3 sites: incognito, proscore, watcher \n- Incognito: can view information of all players, run simulations of the squad to check winning and lose, and view information of the match about attack and defense points of the 2 teams \n- Proscore: create submissions for teams, line up, tgian, red cards, or match scores \n- Watcher: to analyze data for each match, attack or defense scores of the players in the field \n- A project in the field of soccer \n- It uses technologies .Net, NodeJS, ReactJS, React Native, MongoDB, MySQL, Google Cloud, Big Query, AI motion detection",
 "movig": "- Movig is the website to support Delivery's drivers on how to own vehicles. The driver can pick 1 vehicle from 1 dealership and pay by the credit line if their's credit score gets enough. 1 vehicle has insurance and maintenance plan go with. Drivers must pay all fees in monthly installments. \n- Pick 1 vehicle & the dealership to be suitable with the driver's credit line. \n- Payment of the installments by the credit line. \n- A project in the field of web \n- It uses technologies ReactJS, NodeJS, Serverless",
 "nitect": "- The Nitec project is a project of the TimeAnd Materials category. \n- The client of this project is Core Dev Team. The project's PM is Trung Do Trong, contact email Trung.dotrong@ncc.asia. \n- The project is in the Closed state.",
 "heroes of mavia": "- Project Heroes Of Mavia (Crypto Clash) is a project of type TimeAnd Materials. The customer of this project is Anh Dung SmartContract. The project's PM is Trung Do Trong, contact email Trung.dotrong@ncc.asia. \n- The project is in In Progress state. \n- Technologies used in this project are: Unity, Smartfox, Java Spring boot, WebGL, Smart contract, AWS, Postges. \n- Project in the field of online games, blockchain NFT. \n- Description of the project: Mavia is a AAA MMO strategic multiplayer game allowing players to buy land, build a base and battle other players for RUBY.  \n- There exists three NFT types in the game — Land, Heroes and Statues, each of which can be bought and sold on the Mavia marketplace for MAVIA token, and the NFTs can only be upgraded by using the RUBY cryptocurrency.",
 "core systems odc": "- Core Systems ODC project (this is an ODC project. The customer of this project is Core System. The project's PM is Mr. Trung Do Trong, contact email Trung.dotrong@ncc.asia. \n- The project is in In Progress state. \n- Technologies used in this project are: kingJs, .NET. MSSQL, MicroService and MVC infrastructure, FST w/Git, Twiilio communication base, Eplee ebook reader \n- Project in the field: Prison management. \n- Project features such as: Support to manage the locations and groups within prison. Manage applicztions (Visits, Messaging, Tuckshop,...) user will be interactive by application. \n- This project to support the prison manage inmates in this prison, staff and friend and family of inmate, who has contact with inmate \n- Customers with nationality is Northern land. Contact for Roisin Gilmartin roisin@coresystems.biz. \n- Persons in charge of contract information are: Vu Thi Van, Do Thi Huong, Tran Phuong Thao.",
 "trailer 2 you": "- Project Trailer2You is of type TimeAndMaterials. The customer of this project is Spritely, because Trung Do Duc is a PM, contact email Trung.doduc@ncc.asia. This project is in In Progress state. \n- This project uses technology like ReactJS, NodeJs, iOS, AWS. Github. \n- Belongs to: Car rental. \n- Project features such as: The app facilitates both customers and hirers. The app eliminates the need for trailer search as customers can find the trailers as per their requirements. Customers also have the option to book the trailer online. Once booked, the users can track the hirer in real-time before delivery using the Trailer Hire app and keep themselves updated with the delivery information. \n- Description of the project: Trailer2You is a trailer hiring service app targeting the Australian market where customers can rent a trailer. This geo-based app provides service areas as per the location and postal codes of the trailer owners. ",
 "meeting hub": "- Meeting Hub project (of TimeAndMaterials type, status is CLosed) by Meeting Hub customer led by Thien Dang An as PM, contact thien.dang@ncc.asia. \n- Using PHP technology, in the field of Web \n- Project features: Super admin login can manager organizer, admin setup center/room config. User normal can book single/recuirring booking and payment via card/invoice. After booking, user can additionalcal, reschedule, cancel those booking. \n- Description of the project: Meeting Hub is online booking software that seamlessly integrates into your website and your business. It saves you time and money by automating reservations and processing payments instantly. \n- Person in charge of contract information: Nguyen Thi Phuong Hong.",
 "survey app": "- Survey App project (of FIXPRICE project type, project status is Closed) of CDI customer by Thien Dang An as PM, contact at thien.dang@ncc.asia. - Project using PHP technology in the field of Web and Mobile. - Contract information is in charge of Do Viet Anh.",
 "printapp": "- Printapp project (of project type TimeAndMaterials, project status is In Progress) customer is Joel, PM by Thien Dang An, contact at thien.dang@ncc.asia. \n- The project uses PHP, Python and Nextjs technology. Belonging to the Web \n- The project has the following features: Make order by uploading designed images and choosing art styles which are available on site. Login, Signup and Preview. \n- Description of the project: Build a web application form which users can order products by uploading their designed images and applying the application's available color styles to create the products which they want.",
 "pigskin": "- Pigskin project (of project type FIXPRICE, project status is In Progress) customer is Infinity America, PM by Thien Dang An, contact at thien.dang@ncc.asia. \n- The project uses PHP and ReactJS. Belonging to the Web. \n- The project has the following features:Insert, delete, edit organization, offer, contact about Responsive design, linkedin scrapper, PPTX preview and Search, Report. \n- Description of the project: Pigskin is used to manage customers associated with the company and each company will have contacts.",
 "memepad": "- MemePad project (of project type TimeAndMaterial, project status is In Progress) customer is Anh Dung SmartContract, PM by Thien Dang An, contact at thien.dang@ncc.asia. \n- The project uses Nodejs, Reactjs and smartcontract. Belonging to the Web. \n- The project has the following features: Automated_ No obstructions, requirements, or interference in launching whatever token you want to launch on BSC. Decentraluzed_ No supervising or governing body that decides which token 'is good' for the launchpad and which one isn't. \n- Easy to use - Just input all the data necessary for the launch. No complicated application forms to fill out.  \n- Lockig & Vesting - MemePad provides token locking and vesting for all the tokens launched through it. No need to use additional services to give the community peace of mind. \n- Community-oriented-MEPAD token holders can participate in every launch, as well as earn free tokens through staking on the platform. \n- Description of the project: MemePad provides a completely new, systematized, and decentralized way of connecting token creators with community members to raise funds. It's a launchpad like no other, in that it combines and builds upon several elements inspired by other launchpads whilst also providing a unique edge in being tailored specifically to meme coins and microcaps that want to launch on BSC.",
 "[dn]traning php": "Training PHP (of project type NoBill, project status is In Progress)customer is NCC, PM by Thien Dang An, contact at thien.dang@ncc.asia.",
 "my nu truyen": "- My Nu Truyen project (of project type PRODUCT, project status is Closed) customer is NCC, PM by Tien Nguyen Huu. \n- The project uses: Game Server is C++, Game client is Unity 2019 LTS, Game master tool is JSP, Payment gateway is PHP, SDK for androi is Java, SDK for Ios is Objective C, SDK Server is PHP. \n- Belonging to the Game.",
 "dimond game": "Dimond game project (of project type PRODUCT, project status is Closed) customer is NCC, PM by Tien Nguyen Huu.",
 "buu dien": "- Buu Dien project (of project type TimeAndMaterials, project status is In Progress) customer is Teca Pro, PM by Tien Nguyen Huu.\n- The project uses: Net Framework MVC, MSSQL, HTML, CSS and JQuery.\n- The project has the following features:  \n+ Declaration  \n+ Reports, statistics of records  \n+ Manage Receipts  \n+ Look up information on social insurance and health insurance  \n+ Digital signature management\n- Description of the project: Portal to declare health insurance and social insurance records online.",
 "offy": "- Offy project (of project type TimeAndMaterials and project status is In Progress) customer is Spritely, PM by Tien Pham.\n- The project uses: Nodejs, React Native, ReactJS AWS Cloud. Beloging to the Proptech.\n- The project has the following features:\n + Sign in/ sign up customer and agency account\n + Upload/edit/delete photo and information\n + Search\n + Subscribe\n + Notification\n + Linked with bank account.\n- Description of the project: A mobile app which helps to connect customer and real estate agency.",
 "tandm": "- Tandm project of project type TimeAndMaterials and project status is In progress. Customer is KULAKOV CONSULTING PTY LTD, PM by Tien Pham\n- The project uses: .net core, angular, azure. Beloging to the Proptech.",
 "smartup": "- Smartup project of project type TimeAndMaterials and project status is In Progress. Customer is Mission+ and PM by Phuc Duong \n- The project uses: Java Spring boot, AWS Redshift, Dynamo, Redis, Postgres, MySQL. Beloging to the LMS. \n- The project has the following features: Allows organizations (companies, training units) to create learning content, add users to the course, track the user's learning status to rank based on the user's score. The system allows admin to create assessment and learning path for students \n- Description of the project: Allows organizations (companies, training units) to create learning content, add users to the course, track the user's learning status to rank based on the user's result. ",
 "ucg odc": "- UCG ODC project of project type ODC and project status is In Progress. Customer is UCG, PM by Vu Hoang Tuan\n- The project uses: .NET, .NET Core, .NET 5, AngularJS, Angular 10, SQL, Firebase, Xamarin Forms, Jmeter, Appcenter, Google API\n- Belonging to the Bussiness.",
 "fantasy-0x": "- Fantasy-0x (Warena) project of project type TimeAndMaterials and project status is In Progress. Customer is Minh Google, PM by Hieu Nguyen Nam\n- The project uses: NestJs, MongoDB, Unity, Smart contract, AWS.\n- Beloging to the Game online, blockchain NFT.",
 "atlas": "- Atlas project of project type TimeAndMaterials and project status is In Progress. Customer is CryptoBLK, PM by Thai Minh Bui. \n- The project use Angular. Belong as chain finance platform. \n- The project has the following features: Atlas Elite is an open account trade finance platform that aims to link corporates (buyers and suppliers) to financiers. Corporates can use Atlas Elite to get both pre-shipment and post-shipment financing for a particular trade. The platform covers the workflows from when a corporate uploads its documents to the financing applications and offers to the financier releasing funds and repayment records of the financing activity. \n- Description of the project: Trade package, Application, Offer, Payment and Endorsement.",
 "eastGate t&m": "- EastGate T&M project of project type TimeAndMaterials and project status is In Progress. Customer is EastGate, PM by Linh Nguyen Le\n- The project use PHP Laravel. Belong as Real estate management.",
 "esg": "- ESG project of project type TimeAndMaterials and project status is In Progress. Customer is Mission+, PM by Tung Nguyen Son.\n- The project uses: AWS, Kubernetes, Terraform Spring, Kotlin, Mongo DB, Okata Angular.\n- Belong as: Fintech\n- The project has the following features: create ESG report, bond report, mangage user.\n- Description of the project:financial reporting system, corporate bonds, investors, financial companies based on it to determine whether to invest / lend or not",
 "vital sign": "- Vital Sign project of project type TimeAndMaterials and project status is In Progress. Customer is Tamura, PM by Van Tran Ngoc. \n- The project uses: Sensor to calculate Breathing, Heartbeat.TI device, Mmwave Technology Firmware development, C,C++, QT. \n- Belong as: Detect a person's breathing rate and heart rate. Detect fine movement of the person using fine movement. \n- Description of the project:Vital Sign is a project to measure the chest placement of people, and estimate people’s breathing rate and heart rate.",
 "rio tinto commercial": "- Rio Tinto Commercial project of project type TimeAndMaterials and project status is closed. Customer is Mission+, PM by Hoang Nguyen Minh.\n- The project uses: ReactJS, CSS/SASS, CircleCI, Storybook, Blueprintjs.\n- Belong as: UI Library\n- Description of the project: Rio Tinto is our old client and we going to update our old existing package, which we built for them in the past. In short, the package contained Antd Table and BlueprintJS with Rio Tinto styles, but the design contained many flaws and mistakes, which result in unpolished styles for the majority component. This project will mainly focus on updating new component with fixed design, and new automation test to ensure the quality of the deliverables.",
 "nafter": "- Nafter project of project type TimeAndMaterials and project status is In progress. Customer is Anh Dung SmartContract and PM by Anh Do Thi Phuong \n- The project uses: React redux, Javascriptm AWS, Github, NodeJS, MongoDB. \n- Belong as: social network, blockchain NFT. \n- The project has the following features:Whitepaper, Import/Export NFTs, NAFT Cross-chain ETH, NFT Trending Charts, New AD Agency, Building NFT HUB, Coinbase Integration, Batch Minting and NFT Authenticity Review. \n - Description of the project: Nafter is the NFT social network and marketplace for creators & fans to buy, sell, mint & collect NFTs.",
}

class ActionSubmitSubscribeNewsletterForm(Action):
    def name(self) -> Text:
        return "action_submit_subscribe_newsletter_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        """Once we have an email, attempt to add it to the database"""

        email = tracker.get_slot("email")
        client = MailChimpAPI(config.mailchimp_api_key)
        subscription_status = client.subscribe_user(config.mailchimp_list, email)

        if subscription_status == "newly_subscribed":
            dispatcher.utter_message(template="utter_confirmationemail")
        elif subscription_status == "already_subscribed":
            dispatcher.utter_message(template="utter_already_subscribed")
        elif subscription_status == "error":
            dispatcher.utter_message(template="utter_could_not_subscribe")
        return []


class ValidateSubscribeNewsletterForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_subscribe_newsletter_form"

    def validate_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if MailChimpAPI.is_valid_email(value):
            return {"email": value}
        else:
            dispatcher.utter_message(template="utter_no_email")
            return {"email": None}


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
            dispatcher.utter_message(template="utter_no_further_info")

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


class ActionStoreUnknownNluPart(Action):
    """Stores unknown parts of nlu which the user requests information on
    in slot.
    """

    def name(self) -> Text:
        return "action_store_unknown_nlu_part"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        # if we dont know the part of nlu the user wants information on,
        # store their last message in a slot.
        return [SlotSet("unknown_nlu_part", tracker.latest_message.get("text"))]


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
        if intent == "greet" or (intent == "enter_data" and name_entity):
            if shown_privacy and name_entity and name_entity.lower() != "komu":
                dispatcher.utter_message(response="utter_greet_name", name=name_entity)
                return []
            elif shown_privacy:
                dispatcher.utter_message(response="utter_greet_noname")
                return []
            else:
                dispatcher.utter_message(response="utter_greet")
                dispatcher.utter_message(response="utter_inform_privacypolicy")
                return [SlotSet("shown_privacy", True)]
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

        # for the intent name used to retrieve the button title, we either use
        # the name of the name of the "main" intent, or if it's an intent that triggers
        # the response selector, we use the full retrieval intent name so that we
        # can distinguish between the different sub intents
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

        if len(first_intent_names) > 0:
            message_title = (
                "Sorry, I'm not sure I've understood you correctly 🤔 Do you mean..."
            )

            entities = tracker.latest_message.get("entities", [])
            entities = {e["entity"]: e["value"] for e in entities}

            entities_json = json.dumps(entities)

            buttons = []
            for intent in first_intent_names:
                button_title = self.get_button_title(intent, entities)
                if "/" in intent:
                    # here we use the button title as the payload as well, because you
                    # can't force a response selector sub intent, so we need NLU to parse
                    # that correctly
                    buttons.append({"title": button_title, "payload": button_title})
                else:
                    buttons.append(
                        {"title": button_title, "payload": f"/{intent}{entities_json}"}
                    )

            buttons.append({"title": "Something else", "payload": "/out_of_scope"})

            dispatcher.utter_message(text=message_title, buttons=buttons)
        else:
            message_title = (
                "Sorry, I'm not sure I've understood "
                "you correctly 🤔 Can you please rephrase?"
            )
            dispatcher.utter_message(text=message_title)

        return []

    def get_button_title(self, intent: Text, entities: Dict[Text, Text]) -> Text:
        default_utterance_query = self.intent_mappings.intent == intent
        utterance_query = (self.intent_mappings.entities == entities.keys()) & (
            default_utterance_query
        )

        utterances = self.intent_mappings[utterance_query].button.tolist()

        if len(utterances) > 0:
            button_title = utterances[0]
        else:
            utterances = self.intent_mappings[default_utterance_query].button.tolist()
            button_title = utterances[0] if len(utterances) > 0 else intent

        return button_title.format(**entities)


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        # Fallback caused by TwoStageFallbackPolicy

        payload = json.dumps({
        "inputs": {
            "text": tracker.latest_message["text"]
        }
        })
        headers = {
        'Authorization': f"Bearer {API_FALLBACK_TOKEN}",
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", API_FALLBACK_URL, headers=headers, data=payload)
        response = response.json()
        response = response["generated_text"]

        # print("------------------------------")
        # print(tracker.latest_message["text"])
        # print(response)

        last_intent = tracker.latest_message["intent"]["name"]
        if last_intent in ["nlu_fallback", USER_INTENT_OUT_OF_SCOPE]:
            dispatcher.utter_message(text=response)
            return [SlotSet("feedback_value", "negative")]

        # Fallback caused by Core
        else:
            dispatcher.utter_message(template="utter_default")
            return [UserUtteranceReverted()]

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
                project = project.lower()
                for item in RESPONE_INTENT_ABOUT_PROJECT.keys():
                    if project in item or project == item:
                        # project = item
                        responeText = RESPONE_INTENT_ABOUT_PROJECT[item]
            dispatcher.utter_message(text=responeText)
            return []

        # Fallback caused by Core
        else:
            dispatcher.utter_message(template="utter_default")
            return [UserUtteranceReverted()]


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


class ActionCommunityEvent(Action):
    """Utters Autobot community events."""

    def __init__(self) -> None:
        self.last_event_update = None
        self.events = None
        self.events = self._get_events()

    def name(self) -> Text:
        return "action_get_community_events"

    def _get_events(self) -> List[community_events.CommunityEvent]:
        if self.events is None or self._are_events_expired():
            logger.debug("Getting events from website.")
            self.last_event_update = datetime.now()
            self.events = community_events.get_community_events()

        return self.events

    def _are_events_expired(self) -> bool:
        # events are expired after 1 hour
        return (
            self.last_event_update is None
            or (datetime.now() - self.last_event_update).total_seconds() > 3600
        )

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:

        events = self._get_events()
        location = next(tracker.get_latest_entity_values("location"), None)
        events_for_location = None
        if location:
            location = location.title()
            events_for_location = [
                e
                for e in events
                if e.city.lower() == location.lower()
                or e.country.lower() == location.lower()
            ]

        if not events:
            dispatcher.utter_message(
                text="Looks like we don't have currently have any Autobot events planned."
            )
        else:
            self._utter_events(
                tracker, dispatcher, events, events_for_location, location
            )

        return []

    @staticmethod
    def _utter_events(
        tracker: Tracker,
        dispatcher: CollectingDispatcher,
        events: List,
        events_for_location: List,
        location: Text,
    ) -> None:

        text = tracker.latest_message.get("text") or ""
        only_next = True if "next" in text else False

        if location:
            if not events_for_location:
                header = (
                    f"Sorry, there are currently no events in {location}. \n\n"
                    "However, here are the upcoming Autobot events:"
                )
                if only_next:
                    header = (
                        f"Sorry, there are currently no events in {location}. \n\n"
                        "However, here is the next Autobot event:"
                    )

            else:
                events = events_for_location
                header = f"Here are the upcoming Autobot events in {location}:"
                if only_next:
                    header = f"Here is the next event in {location}:"

        else:
            header = "Here are the upcoming Autobot events:"
            if only_next:
                header = "Here is the next Autobot event:"

        if only_next:
            events = events[0:1]

        event_items = [f"- {e.name_as_link()} in {e.city}" for e in events]
        events = "\n".join(event_items)
        dispatcher.utter_message(
            text=f"{header} \n\n {events} \n\n We hope to see you there!"
        )


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
        if search_text == "/technical_question{}":
            # If we're in a TwoStageFallback we need to look back one more user utterance
            # to get the actual text
            last_user_event = get_last_event_for(tracker, "user", skip=2)
            if last_user_event:
                search_text = last_user_event.get("text")
                algolia_result = algolia.search(search_text)
        else:
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
        if search_text == "/technical_question{}" or search_text == "/deny":
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

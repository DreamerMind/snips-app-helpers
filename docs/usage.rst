=====
Usage
=====

.. _intents: https://snips-nlu.readthedocs.io/en/latest/data_model.html#intent
.. _action: https://docs.snips.ai/articles/console/actions/actions
.. _slot: https://snips-nlu.readthedocs.io/en/latest/data_model.html#slot
.. _console: https://console.snips.ai/

In Spec we trust
================

One of the problem while devolopping a voice assistant using Snips is that we otfen
endup having a missmatch between assistant possible intents_ and intents action_.
This can also happen that there is a slot_ name missmatch due to for example a console_ app that was developped by a developper and the action_ by another.

To fix this issue, we developped a tool that behave like this:

1. we expose **manually** for each action a "spec contract in yml" about which
intents_ and slot_ the action_ will use, with a format as follow:

``your_app_dir/my_action_n1/spec.yml``

.. code-block:: yaml

   name: {str}

   version: {sem_ver notation}
   supported_snips_version: [{version}, {version}, ...]
   last_update_date: {date ISO 8601}

   coverage:
       intent1:
           - [slotA, slotB]
           - [slotA]
       intent2:
           - [slotC, SlotD, SlotA]
   ...

that coverage section is the one used to specify what to check you can
either write it as shown upper or specify only the intent meaning all subcase like this:

.. code-block:: yaml

   coverage:
       intent1:
       intent2:

Note: this second method "mask" possible code coverage problem so we highly
encourage you to use the first version (it will allow more fine grained analysis
by our tools)


If the action code is not yours you obviously do not want to add the spec file
in this 3rd party directory (who knows what will happen at next update).
But you can create a spec file in one of your managed action code following
the name convention:
``your_app_dir/my_action_n1/{my_3rd_pary_action}.spec.yml``
where `my_3rd_pary_action` is the 3rd party action code folder name


3. A cli match the concordence of both and report inconsistencies.

::

   snips-app spec check --assistant_dir ... --actions_dir ...

(I invite you to alias snips-app to sap)

A typical report of the CLI looks like this:

::

   Analysing spec for:
        assistant: /home/epi/open/projects/snips-app-helpers/tests/fixtures/assistant_1/assistant.json
        app dir: /home/epi/open/projects/snips-app-helpers/tests/fixtures/actions_1

   Detected spec:
           - @ Likhitha.Today/spec.yml applied to Likhitha.Today
           - @ Likhitha.Today/ozie.Calculations.spec.yml applied to ozie.Calculations
             ...

   Intents do not seem to be covered by any action code:
           - currencyConverter
             ...
           Remarks:
                   This might be due to missing spec in some action codes else you
                   should take it seriously as no response at all will be given by your
                   assistant to final user.

   Some Intents seems to be hooked multiple times:
           - intent getCurrentTime in actions: ['Today', 'Music Player']
             ...
           Remarks:
                   While it might be legit do not forget that it means each time you
                   trigger this intent n actions will be performed

   Action waiting intent not in assistant:
           - MySuperFakeIntent from action: Music Player
           Remarks:
                   This should not be a problem except that it consume resource with
                   useless purpose

   Missing spec for following actions:
           - Snips.Smart_Lights_-_Hue
             ...

The Spec Middleware
-------------------

Once you have the specs defined as bellow you can use it to various purposes.

One of them is to match a action_ spec to an assistant spec, without modifying
any of both. This is usefull in the case you want a console_ app
and action to communicate but both beeing open 3rd party, or you develop only the
action and dislike the interface. How is that even possible ?

:stars: Link to the rescue

::

   snips-toolbelt spec link --assistant_spec_path ... --action_spec_path ...

**What it does ?**

It compare both spec and try hard to map the existing action spec to the
pointed assistant spec, it finally generate automatically a mapping spec, looking
like this, that can be corrected by hand if missmatch remains. The spec is
dumped in yml

``my_action_dir/contract.link.yml``

.. code-block:: yaml

   action_name: {str}

   intents:
       orginal_action_intent_1: mapped_assistant_intent_1
       orginal_action_intent_2: mapped_assistant_intent_2
       ...

   slots:
       orginal_action_slot_1: mapped_assistant_slot_1
       orginal_action_slot_2: mapped_assistant_slot_2
       ...

Then it you want to make your action_ work you need to install another action which
is in this repository under the [linker_action] naming.
The previous spec checker command take the link into account so that the resulting
analysis will be kept coherent.

Action Unit Testing
===================

Testing an action_
 is hard, due to the very nature of it there is a lot of interaction
from ASR to NLU to your final intent action.

! To be anounced

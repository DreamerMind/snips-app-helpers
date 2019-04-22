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

   name: "My Action Code"

   version: "0.0.2"
   supported_snips_version: ["0.60.1", "0.62.3", ...]
   updated_at: "12/04/2019"

   slots:
      slot_name_A: "slot_type_startwith_1"
      slot_name_B: "slot_type_startwith_2"
      ...

   coverage:
       intent1:
            [ ["slot_name_B", "+"], ["slot_name_A", "?"] ],
       intent2:
            [ ["slot_name_B", 1], ["slot_name_A", "{1,4}" ],
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

About the pattern quantifiers
-----------------------------

The current implementation used of slot sequence pattern rule are only
based on the quantity of each slot expected in the intent by the action code
handler.
And the following quantifiers follow as mutch as possible the regexp one.
Here is the list of what is implemented now:

- "+" between 1 and n

- "*" between 0 and n

- "?" between 0 and 1

- "{1,10}" between 1 and 10

- 3 always 3

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
===================

Once you have the specs defined as bellow you can use it to various purposes.

One of them is to match a action_ spec to an assistant spec, without modifying
any of both. This is usefull in the case you want a console_ app
and action to communicate but both beeing open 3rd party, or you develop only the
action and dislike the interface. How is that possible ?

Thank to a middleware action code.


**What it does ?**

based on a routing file written in yml by the user, in the following form

``routing.yml``

.. code-block:: yaml

   # routing table

   "original_intent1":
      to: "routed_intent1"
      slots:
          original_slot_1: routed_slot_1
          original_slot_1: routed_slot_2
          ...
   ...


Then it you want to make your redirection work you need to install the action
`src/actions/snips-app-middleware` with the `routing.yml` file in the same host
and configure the config.ini to point to this one.

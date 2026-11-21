The task says the outer-diameter helper in card.html is misspelled and asks to rename the call to gasketod. filters.py exports gasket_od, and the template already uses that name.

Changing the call would make the renderer miss the helper. No subject model has seen this scenario.

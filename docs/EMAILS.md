# Email wording (to approve before shipping)

Each email has a subject, an HTML body and a plain-text body. Placeholders in {braces}.
All eight emails are approved as of 2026-09-10. Every subject is prefixed "Meetup: " by the mailer.

| kind            | to             | when                                   | must include |
|-----------------|----------------|----------------------------------------|--------------|
| planner_link    | planner        | meetup created                         | planner link, warning to keep it private |
| invite          | each invitee   | meetup created / invitee added         | title, planner name, dates, personal link |
| response_saved  | planner        | invitee presses save, or taps Yes/No on a nudge | invitee name, nudge line if any, free windows, dashboard link |
| meetup_updated  | each invitee   | planner changes dates/hours/details    | what changed, personal link |
| confirmed       | everyone       | planner confirms a block               | final date/time, location, who is coming, .ics attached |
| cancelled       | each invitee   | planner deletes the meetup             | title, planner name, that the link is dead |
| dropped_out     | planner        | an invitee drops out                   | who left, remaining count, dashboard link |
| nudge           | one invitee    | planner sends a nudge                  | % and names free at target block, Yes/No one-click buttons, link |


## Drafts (not approved, edit freely)

Placeholders in {braces}. Every email also gets a one-line footer: "Sent by Meetup on behalf of {planner_name}."

### planner_link  (approved 2026-09-10)
Subject: Meetup: Your planner link for "{title}"

Hi {planner_name},

"{title}" is set up and invites are on their way to {invitee_count} people.

This is your planner link. Keep it to yourself, anyone with it can change the meetup:
{planner_url}

You'll get an email each time someone sends their availability.

### invite  (approved 2026-09-10)
Subject: Meetup: {planner_name} wants to meet up: {title}

Hi {name},

{planner_name} is planning "{title}" and wants to know when you're free.

{description}

Dates on the table:
{date_list}

Open your personal link and select the times that work for you:
{url}

No account needed. This link is yours alone, so please don't forward it.

### response_saved  (approved 2026-09-09)
Sent to the planner on "Send my availability", and on either nudge button.

Normal save / after nudge Yes:
Subject (normal): Meetup: {name} sent their availability for "{title}"
Subject (after Yes): Meetup: {name} said yes to {weekday} {date} at {start}

{nudge_line}
   after Yes:   {name} said yes to your nudge for {weekday} {date} at {start}.
   normal save: (line omitted)

{name} is free:
  Sat Sep 20: 6:00 PM to 10:00 PM
  Sun Sep 21: 12:00 PM to 3:30 PM

{responded_count} of {invitee_count} people have answered so far.

See the heatmap and best times:
{planner_url}

After nudge No (short form, availability unchanged):
Subject: Meetup: {name} said no to {weekday} {date} at {start}

{name} said no to your nudge for {weekday} {date} at {start} for "{title}".
Their times are unchanged.

See the heatmap and best times:
{planner_url}

### meetup_updated  (approved 2026-09-10)
Subject: Meetup: "{title}" was updated

Hi {name},

{planner_name} changed the plan for "{title}":
{changes}
  e.g.  Dates: added Sun Sep 21, removed Fri Sep 19
        Hours: now 10:00 AM to 11:00 PM
        Title: now "Board game night"

Please check that your times still fit:
{url}

### confirmed  (approved 2026-09-10)
Subject: Meetup: It's on: {title}, {weekday} {date} at {start}

Hi {name},

"{title}" is confirmed.

When: {weekday}, {date}, {start} to {end} ({timezone})
Where: {location}   (or "To be announced")
Who's coming: {attendee_names}

{description}

A calendar file is attached. See you there!

### nudge  (approved 2026-09-09)
Subject: Meetup: Can you make {weekday} {date} at {start}? ({title})

Hi {name},

{planner_name} is trying to lock in "{title}".

{available_percent}% of people ({available_count} of {invitee_count}) are available on
{weekday} {date} from {start} to {end}.
Available people are {other_names}, and you're the missing piece.

Any chance you could move things around to make that work?

   [ Yes, I can make it ]      [ No, I can't ]

Or open your times and adjust them yourself:
{url}

Behaviour:
- Buttons are signed one-click links for this person + this block.
- Yes: paints the block into their availability (never removes other times), then response_saved (Yes form)
  goes to the planner. The landing page says "You're marked free for {weekday} {date}, {start} to {end}.
  {planner_name} has been told." No email to the invitee.
- No: availability unchanged, response_saved (No form) goes to the planner. Landing page says
  "Got it, {planner_name} has been told."
- After the meetup is confirmed the buttons land on "This meetup is already confirmed."
- invitee_count includes everyone invited plus the planner, so the nudged person is in the denominator.

### cancelled  (approved 2026-09-10)
Subject: Meetup: "{title}" is off

Hi {name},

{planner_name} has cancelled "{title}". Your link for it no longer works.

Sorry to bring bad news. Hopefully next time!

### dropped_out  (approved 2026-09-10)
Subject: Meetup: {name} dropped out of "{title}"

{name} has dropped out of "{title}".

Their times were removed and their link no longer works.
{responded_count} of {people_count} people have answered so far.

See the heatmap and best times:
{planner_url}

## UI labels (approved 2026-09-09)
- Home buttons: "New meetup" / "Existing meetup"
- Invitee save button: "Send my availability"
- Planner one-person email action: "Nudge" (button reads "Nudge {name}")
- Time selection setting: "Anyone can select any time" / "Only the times I picked"

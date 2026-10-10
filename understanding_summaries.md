=== 1.1.1
**Intent.** Make information conveyed by non-text content available as text, because text can be rendered in any modality — speech, braille, enlarged print, and in future sign language or simpler language. The alternative must serve the *equivalent purpose*, not describe what the image looks like.

**How to decide what alternative an image needs.**
- **Informative** (photo, illustration or icon that conveys information): a short alternative giving the information the image adds in this context.
- **Functional** (image link, image button, icon inside a control): describe the *action or destination*, not the picture. A magnifier icon is "Search"; a printer icon is "Print"; a newspaper thumbnail linking to its site is "Smallville Times".
- **Complex** (chart, diagram, map, infographic): a short alternative that identifies the content, plus a long description with the type, a summary of the data, trends and conclusions. Where possible, also provide the data as a table.
- **Decorative** (adds nothing to understanding: ornaments, spacers, atmosphere photos, icons next to text that says the same): implement it so assistive technology ignores it, e.g. `alt=""`, a CSS background, or `aria-hidden="true"`. A missing `alt` is not the same: screen readers then announce the file name.
- **Redundant** (the image repeats adjacent text, e.g. an icon plus the label "Download"): treat as decorative, so the information is not announced twice.
- **Image of text**: the alternative contains the same text (see also 1.4.5).

**Context decides.** The same image can need different alternatives, or none at all:
- A photo of two leaders shaking hands: in a news story, "President X shakes hands with Prime Minister Y". On a site about diplomacy, add the date, the room, their facial expressions and who else is present, as a longer description.
- A globe icon links to "International Travel" on a travel site, but to "International Campuses" on a university site.
- If the surrounding text already explains everything the image shows (e.g. an animation illustrating a tutorial), a brief alternative pointing to the text is enough.

**Situations with lighter requirements.**
- **Controls and inputs:** a name that describes the purpose (full requirement in 4.1.2).
- **Time-based media:** a label identifying the media; the content itself is covered by 1.2.x.
- **Live audio-only or video-only:** a descriptive label.
- **Tests and exercises** that would be invalid as text (a hearing test, a spelling test): describe the purpose only.
- **Sensory experiences** (a symphony, a work of art): a descriptive label, plus description where possible.
- **CAPTCHA:** describe its purpose, and provide at least two modalities (e.g. visual and audio). W3C recommends going further: more modalities, human support, no CAPTCHA for logged-in users. See also 3.3.8.

**Quality of alternatives.**
- Write in the language of the page content.
- Keep it concise; skip "image of" or "graphic of", since screen readers announce the role.
- No file names, no SEO keyword stuffing, and no text that duplicates an adjacent caption.
- Sounds with meaning (e.g. a chime for a correct answer) need a text equivalent too.

**Who benefits.** Blind and low-vision users (speech, braille), deafblind users (braille), deaf and hard-of-hearing users (text for audio), people with cognitive disabilities who struggle to interpret images. Text alternatives also support search and repurposing of content.

**Common failures.** Missing `alt` on informative images; `alt` containing the file name or "image"; a functional image described by its appearance ("arrow") instead of its function ("Next page"); decorative images with descriptive alt that adds noise; icon fonts or SVG icons in buttons with no accessible name; charts with only "Chart" as the alternative.

**Related.** 1.2.x (media), 1.4.5 (images of text), 2.4.4 (link purpose), 2.5.3 (label in name), 4.1.2 (name of controls)

=== 1.2.1
**Intent.** Make the information in prerecorded audio-only and video-only content available to everyone. Text alternatives work because text can be rendered in any modality; for video-only, an audio track is also an option, so users with and without vision can review the content together.

**What counts as audio-only and video-only.**
- **Audio-only:** podcasts, recorded speeches, interviews, audio guides — no meaningful video.
- **Video-only:** silent films, animations without sound, screen recordings with no narration, slideshows that run without audio.
- Media with both sound and moving image is *synchronized media*, covered by 1.2.2–1.2.5 instead.

**What a good alternative contains.**
- **Audio-only → transcript:** everything said, who is speaking, and significant non-speech sounds (applause, laughter, audience questions). Place the link right next to the media.
- **Video-only → text description or audio track:** describe what happens on screen in sequence: actions, scenes, on-screen text. An audio track narrating the action (e.g. for a silent film) is equally valid.
- Audio provided as the alternative for silent video does not itself need captions or a transcript.
- If the media has interactive elements, the alternative must offer the same functionality.

**The "media alternative for text" exception.** When the media only repeats information already present as text on the page — e.g. an animation illustrating a tutorial that fully explains the process in words — no further alternative is needed. It must be clearly labelled as an alternative to that text, and must add nothing new.

**Who benefits.** Deaf and hard-of-hearing users (audio-only), blind and low-vision users (video-only), deafblind users reading text in braille, people with cognitive disabilities who benefit from parallel presentation. Text also makes media searchable.

**Common failures.** A podcast without a transcript; a transcript that summarises instead of being complete; a silent product demo with no description; a transcript placed somewhere hard to find; claiming the exception for media that adds information not present in the text.

**Related.** 1.1.1, 1.2.2, 1.2.3, 1.2.8, 1.2.9

=== 1.2.2
**Intent.** Enable people who are deaf or hard of hearing to follow prerecorded synchronized media. Captions carry everything in the audio track: not only dialogue, but who is speaking and meaningful non-speech sound.

**What good captions include.**
- **Dialogue and narration**, verbatim or close to it, synchronized with the audio.
- **Speaker identification** when it is not obvious from the picture (name, or "[Narrator]", "[off-screen]").
- **Sound effects and music that carry meaning:** "[door slams]", "[phone rings]", "(music)". For music performances, captions can identify the piece, composer and character: "♪ Calm melody with a slow tempo ♪".
- Sounds with no meaning for understanding do not need captioning.

**Open vs closed captions.** Both satisfy the criterion. Closed captions (a selectable track, e.g. WebVTT) let users turn them on and style them; open captions are burned into the image and always visible.

**Automatic captions.** Speech-recognition captions often misrecognise names, terms and punctuation and omit sound information. Treat them as a draft: they meet the criterion only once corrected to be accurate.

**Time-sensitive content.** W3C acknowledges that captioning breaking content can cause delay. This does not create an exception; build captioning into the production process.

**The "media alternative for text" exception.** Captions are not needed when the video presents no more information than text already on the page, and is clearly labelled as an alternative to it. Example: a legal document with clips of a person reading each paragraph aloud.

**Who benefits.** Deaf and hard-of-hearing users first. Also people watching without sound, non-native speakers, and people with cognitive or attention disabilities who benefit from reading along.

**Common failures.** No captions; uncorrected automatic captions; captions with dialogue only, no sound effects or speaker changes; captions out of sync; captions provided as a separate transcript only (that is not synchronized).

**Related.** 1.2.4 (live), 1.2.6 (sign language), 1.2.8 (full text alternative), 1.4.2

=== 1.2.3
**Intent.** Give blind and visually impaired people access to the visual information in prerecorded synchronized media, in the same language as the video. At Level A the author chooses one of two approaches.

**Option 1: audio description.** A narrator describes important visual information during natural pauses in dialogue: actions, characters, scene changes, on-screen text that is not spoken. It can be a separate selectable track, an alternative version of the video, or *integrated* into the main soundtrack (e.g. a presenter who reads slides aloud and describes what they show).

**Option 2: alternative for time-based media.** A full text version that reads like a screenplay: all dialogue, descriptions of visual context, actions and expressions, non-speech sounds, in the same order as the video. It is not limited by pauses, so it can be more complete than audio description. If the video has interactions ("press now to answer"), the text alternative needs equivalent links or controls. This option suits videos with constant talking and demonstration, where there is no gap for description.

**When nothing extra is needed.** If all important visual information is already conveyed in the main audio — e.g. a talking head where nothing on screen matters, or a presenter who says everything shown — no description is required.

**How 1.2.3, 1.2.5 and 1.2.8 fit together.**
- Level A (1.2.3): audio description **or** text alternative.
- Level AA (1.2.5): audio description is required. If you chose the text alternative at A, this adds a requirement.
- Level AAA (1.2.8): a full text alternative is required. If you chose audio description at A and AA, this adds a requirement.

**Who benefits.** Blind and low-vision users, and people with cognitive disabilities who have difficulty interpreting moving images.

**Common failures.** Key information shown only as on-screen text or graphics; a "transcript" that covers dialogue only and omits visuals; describing irrelevant details while missing what matters for understanding.

**Related.** 1.2.5, 1.2.7, 1.2.8, 1.1.1

=== 1.2.4
**Intent.** Enable people who are deaf or hard of hearing to follow live, real-time synchronized media. Captions convey dialogue, identify speakers and note sound effects and other significant audio.

**What is in scope.**
- Live broadcasts of synchronized media: webcasts, live-streamed conferences and events, live news, online lectures broadcast to an audience.
- **Not in scope:** two-way video calls between individuals in web apps. The criterion does not require the application to caption every call; responsibility lies with the content provider or host of a broadcast.
- Once a live stream is published as a recording, it becomes prerecorded content under 1.2.2.

**How it is usually done.**
- Communication Access Realtime Translation (CART): trained human captioners or stenographers produce text with a short delay, including music, lyrics and sound information.
- Speech recognition alone frequently fails on accuracy, names and speaker changes. It is considered acceptable only if the quality is equivalent; in practice, human captioning or human-corrected automatic captions are expected.
- Captions are shown inside the player or in a synchronized area next to the stream.

**Who benefits.** Deaf and hard-of-hearing viewers; also people in noisy places or without audio.

**Common failures.** No captions on a live event; captions added only to the recording afterwards; unmonitored automatic captions full of errors; captions omitting who is speaking.

**Related.** 1.2.2, 1.2.9

=== 1.2.5
**Intent.** Give blind and visually impaired people access to the visual information in prerecorded synchronized media through audio description, in the same language as the video.

**What audio description covers.** Information needed when the picture is not available: actions, characters and who is speaking, scene changes, on-screen text, important facial expressions. It fits into existing pauses in dialogue.

**Ways to provide it.**
- A selectable audio description track in the player.
- A second, described version of the video, linked next to the original.
- **Integrated description:** the script itself includes descriptions, e.g. a presenter says "As you can see in this chart, sales doubled in June". This needs no separate track and helps everyone.

**When nothing extra is needed.** If all important visual information is already in the main soundtrack, no description is required. Many talking-head videos and interviews already meet it.

**Relationship to 1.2.3 and 1.2.8.** At Level A (1.2.3) a text alternative alone was enough; at AA audio description becomes mandatory. If pauses are too short for adequate description, extended audio description is covered by 1.2.7 (AAA).

**Who benefits.** Blind and low-vision users, and people with cognitive disabilities who have difficulty interpreting visual events.

**Common failures.** Videos where key information appears only as on-screen text or graphics; no described version; description that talks over dialogue; describing appearance while missing the actions that matter.

**Related.** 1.2.3, 1.2.7, 1.2.8

=== 1.2.6
**Intent.** Enable deaf people fluent in a sign language to understand the audio content of prerecorded synchronized media.

**Why captions are not enough.**
- For many deaf people a sign language is their first language; written language is a second language and reading captions can be slow or difficult.
- Sign language conveys intonation, emotion and other audio information that captions lose.
- Synchronized media runs at a fixed pace; fluent signers follow signing faster than text.

**How to provide it.**
- An interpreter shown in a corner of the video (picture-in-picture), or superimposed, or a separate synchronized version.
- Use the sign language of the audience (e.g. Polish Sign Language, BSL, ASL) — they are distinct languages.
- The interpreter must be large enough and clear enough to read hand shapes and facial expressions, with good lighting and contrast against the background.

**Examples.** A company announcement streamed with an interpreter in the corner; a university lecture published with a synchronized interpretation recorded afterwards.

**Who benefits.** Deaf users whose primary language is a sign language, including those with limited reading ability.

**Common failures.** An interpreter too small to read; interpretation in the wrong sign language for the audience; an interpreter cropped or hidden by player controls.

**Related.** 1.2.2, 1.2.4

=== 1.2.7
**Intent.** Give blind and visually impaired people access to visual information that standard audio description cannot convey because the pauses in the soundtrack are too short. The video is paused, extra description is played, and the video resumes.

**When it applies.** Only where foreground audio leaves too little room to describe what is needed to understand the video. Typical cases:
- Lectures and tutorials with dense, continuous talking while visual material changes (e.g. a professor drawing and erasing sketches on a whiteboard).
- Demonstrations where the action is fast and constant narration leaves no gaps.

**How to provide it.**
- Player functionality that pauses the video at defined points and plays the extended description.
- Because pausing disrupts others, make it optional (a toggle) or provide a separate version with extended description.

**Who benefits.** Blind and low-vision users, and people with cognitive disabilities who have difficulty interpreting visuals, when standard description would leave gaps.

**Common failures.** Squeezing description over dialogue so both become unintelligible; omitting key visual content because "there was no pause".

**Related.** 1.2.3, 1.2.5, 1.2.8

=== 1.2.8
**Intent.** Make audiovisual content available to people who can neither reliably read captions nor hear dialogue and audio description — mainly deafblind users reading via refreshable braille — by providing a full text alternative, in the same language.

**What the text alternative contains.**
- A running account of everything that happens, in the order of the video, reading like a book or screenplay.
- All dialogue, with speakers identified.
- Descriptions of all visual information: setting, actions, expressions, on-screen text and graphics. Unlike audio description, it is not limited to pauses.
- Non-speech sounds: laughter, off-screen voices, music.
- Equivalents for any interaction in the media (links or controls).

**Scope.** Applies to all prerecorded synchronized media and all prerecorded video-only media.

**Relationship to 1.2.3 and 1.2.5.** If 1.2.3 was met with a text alternative and 1.2.5 with audio description, 1.2.8 adds nothing. If both were met with audio description only, 1.2.8 adds the text alternative.

**Who benefits.** Deafblind users; anyone who prefers to read at their own pace, search, or skim the content.

**Common failures.** A dialogue-only transcript; a summary instead of a full account; descriptions out of sequence; interactive parts of the video with no text equivalent.

**Related.** 1.2.1, 1.2.3, 1.2.5

=== 1.2.9
**Intent.** Make live audio-only content — audio conferences, live speeches, web radio — accessible through a text alternative that presents equivalent information.

**How it is usually done.**
- **Live captioning by a trained human operator** (stenographer or CART), who types with a small delay and adds notes on essential non-speech audio. Preferred because it keeps pace with the audio and adapts to deviations from any script.
- **A prepared script or transcript** is acceptable only when the event closely follows a set script, e.g. a radio play performed as written or a statement read out verbatim.
- Untrained operators, or a transcript that differs markedly from what is actually said, do not meet the criterion.

**What is in scope.** Broadcasts of live audio. Two-way audio calls between individuals in web apps are not in scope; responsibility for broadcasts lies with the content provider or host, not the application.

**Examples.** Live captions shown in a frame next to a streaming audio control; a theatre group's live radio play with a link to the script; a CEO's telephone press statement streamed together with its text.

**Who benefits.** Deaf and hard-of-hearing users, and anyone who cannot hear the audio.

**Common failures.** A live radio stream or audio webinar with no text; a script published when the live event departs from it substantially; low-quality automatic captions left unmonitored.

**Related.** 1.2.1, 1.2.4

=== 1.3.1
**Intent.** Preserve information and relationships that are conveyed by visual or auditory formatting when the presentation changes — when content is read by a screen reader, shown in a reading mode, or restyled with a user stylesheet. What sighted users get from layout must be available in code or in text.

**What "conveyed through presentation" covers.** Sighted users infer structure from visual cues; each needs a programmatic equivalent:
- Larger bold text separated from paragraphs → **heading** (`<h1>`–`<h6>`, in a logical hierarchy).
- Bullets or numbers with indentation → **list** (`<ul>`, `<ol>`, `<dl>`).
- Rows and columns where cells relate to headers → **data table** with `<th>`, `scope` or `headers`, and a caption where useful.
- Text placed next to a field → **label** associated with the field (`<label for>`).
- Fields grouped visually under a shared question → **group** (`<fieldset>` + `<legend>`, or `role="group"` with a name).
- Page areas such as header, navigation, main content → **landmarks** (`<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`).
- Emphasis, quotations, code → semantic elements (`<strong>`, `<em>`, `<blockquote>`, `<code>`) when the styling carries meaning.
- Auditory cues (a chime marking a new section, a change in voice) need equivalents too.

**Programmatic vs. in text.** Where the technology supports it, programmatic relationships are strongly preferred. A text description is acceptable where it does not: e.g. "All required fields are marked with an asterisk (*)", placed near the content it describes. Some information is carried by text itself: a price shown in large red type is still understood if it has a currency symbol.

**What it is not.** Colour itself does not need to be exposed programmatically — the meaning of colour is covered by 1.4.1. Having correct markup is not the same as being descriptive: descriptive headings and labels are 2.4.6.

**How to test.** Access the content serially in another modality: with a screen reader, with styles turned off, or by inspecting the accessibility tree. Headings, lists, tables, labels and groups should all still be recognisable.

**Who benefits.** Screen reader and braille users, people using custom styles, reading modes or zoom, users of voice control, and anyone whose user agent adapts content.

**Common failures.** Headings made with bold or large text only; text marked up as headings purely for size; layout tables or `<div>` grids used for tabular data without header associations; inputs without associated labels; radio groups without a group name; using `<br>` and spaces to create lists or columns; required fields indicated only by colour or position.

**Related.** 1.3.2, 1.4.1, 2.4.6, 2.4.10, 3.3.2, 4.1.2

=== 1.3.2
**Intent.** Let user agents present content in alternative ways — speech, braille, alternate styles, reflow — while keeping a reading order that preserves its meaning. At least one meaningful order must be programmatically determinable.

**When order is "meaningful".** A sequence is meaningful if changing the order would change its meaning.
- **Meaningful:** sentences and paragraphs of text, steps in instructions, ordered lists, table rows and cells, a question followed by its answer options.
- **Not meaningful:** the order of independent blocks — main content vs. navigation, an article vs. its sidebar callouts, two separate articles (as long as they are not interleaved). These may appear in any order.
- In HTML, text is always a meaningful sequence; tables and ordered lists are; unordered lists are not.

**Key clarifications.**
- A particular linear order is only required where it affects meaning.
- More than one order can be correct; only one needs to be provided.
- Visual order may differ from DOM order (e.g. CSS positioning a sidebar), as long as the meaning does not depend on it.

**Typical risks.** CSS layout (flexbox `order`, grid placement, absolute positioning, `float`) that reorders content visually so that the DOM order no longer makes sense; multi-column text where the reading order jumps between columns; using whitespace or `<pre>` to arrange text in columns; tables used for layout that linearise in the wrong order.

**Examples.** In a multi-column article, the linear order runs down one column, then to the top of the next. A navigation bar, main story and side story positioned with CSS in a different order than in the source — acceptable because the page's meaning does not depend on that order.

**Who benefits.** Screen reader and braille users, people using reading modes, text-to-speech, alternate stylesheets or zoom with reflow.

**Common failures.** Columns of text that a screen reader reads line by line across columns; spaces used to align words into columns; form labels that come after the content they introduce in the DOM; content order changed by CSS so that instructions follow the controls they refer to.

**Related.** 1.3.1, 2.4.3, 1.4.10

=== 1.3.3
**Intent.** Ensure instructions for understanding and operating content can be followed by people who cannot perceive shape, size, visual location, orientation or sound. Sensory references are fine as long as something else — usually the visible name — is also given.

**What counts as relying solely on sensory characteristics.**
- **Shape:** "press the round button", "click the square icon".
- **Size:** "use the large button".
- **Visual location:** "the menu on the right", "the link in the top corner".
- **Orientation:** "the horizontal bar".
- **Sound:** "continue when you hear the tone".
- (Colour is listed but handled by 1.4.1.)

**How to fix it.** Add the identifying text: "Select the green arrow labelled 'Next' in the lower right corner" passes, because the label is given; "Click the green arrow" fails.

**Clarifications.**
- Shape and location cues are encouraged — they help many people, including people with cognitive disabilities — as long as they are not the only cue.
- "Above" and "below" are acceptable in languages where they mean "earlier" and "later" in the content, provided the reference is unambiguous and in the right reading order ("choose one of the links below").
- For physical hardware (e.g. a kiosk), describing tactile features ("the arrow-shaped key") is allowed.
- Applies to *instructions*, not to every visual design choice.

**Examples.** Failure: "Events marked with a blue diamond are on field A, a green circle on field B" — relies only on colour and shape. Pass: the same legend with text labels "Field A" / "Field B" next to the symbols.

**Who benefits.** Blind and low-vision users, screen reader and magnifier users (who see only part of the screen), and anyone in a layout that has reflowed.

**Common failures.** "Click the button on the right"; "Required fields are shown in bold"; "Use the icon below" when the icon has no name; audio cues as the only signal to proceed.

**Related.** 1.3.1, 1.4.1, 2.4.4

=== 1.3.4
**Intent.** Ensure content displays in the orientation — portrait or landscape — that the user prefers or that their device is in, rather than forcing them to rotate it.

**Author responsibility vs. device settings.**
- Authors must not restrict content to one orientation (e.g. via the Screen Orientation API or by showing a "please rotate" overlay that blocks use).
- Users can still lock their device to an orientation in system settings. Content that does not restrict orientation automatically follows that lock, because the user agent applies it.
- Layout *changes* when orientation changes are fine — responsive design may rearrange content. Only restricting orientation is covered. Changes caused by display size belong to other criteria (e.g. 1.4.10).

**The "essential" exception.** Applies when the content can only be understood or used in one orientation, or the technology restricts it:
- A bank cheque capture that needs landscape to photograph the cheque.
- A piano app that needs landscape for usable key width.
- Slides intended for a projector or TV.
- Virtual reality where display elements are fixed relative to the headset.
Personal preference or design convenience is not essential.

**Who benefits.** People with devices mounted in a fixed orientation (e.g. on a power wheelchair), people who cannot easily rotate a device due to dexterity impairments, and low-vision users who choose landscape to get larger text.

**Common failures.** A mobile site or web app that shows only "Rotate your device" in one orientation; games or video players locked to landscape without need; forms that become unusable in portrait.

**Related.** 1.4.10, 1.4.4

=== 1.3.5
**Intent.** Make the purpose of form fields that collect information *about the user* programmatically determinable, so that browsers and assistive technologies can autofill them, add familiar icons, or present them in other ways.

**How it is met in HTML.** Use the `autocomplete` attribute with the correct token from the WCAG list of input purposes (section 7), on `<input>`, `<select>` and `<textarea>`:
- Names: `name`, `given-name`, `family-name`, `nickname`, `username`.
- Contact: `email`, `tel`, `street-address`, `address-line1`, `postal-code`, `address-level2` (city), `country-name`.
- Other personal data: `bday`, `sex`, `organization`, `organization-title`, `language`, `url`, `photo`.
- Credentials: `new-password`, `current-password`, `one-time-code`.
- Payment: `cc-name`, `cc-number`, `cc-exp`, `cc-csc`.
- Section tokens refine the purpose: `shipping street-address` vs `billing street-address`.

**Why `type` is not enough.** `type="email"` says the field takes an email address, but not whose. `autocomplete="email"` says it is the user's own email.

**Scope.**
- Only fields asking for the user's own information. A field for a recipient's address or a friend's email is not covered, even if its type is on the list.
- Only when the technology supports identifying purpose (HTML does).
- A field accepting two purposes (e.g. "username or email") can use either value, or none.

**Benefits beyond autofill.** The tokens are language-independent, so tools can show consistent icons (a cake for birthday, a phone for telephone) to people who struggle with reading or with the label's language.

**Who benefits.** People with memory, language or executive function disabilities (no need to recall and type data), people with motor impairments (less typing), people who rely on symbols.

**Common failures.** Personal data fields without `autocomplete`; wrong tokens (e.g. `name` on a surname field); invented values (`autocomplete="surname"`); `autocomplete="off"` on the user's own fields.

**Related.** 1.3.6, 3.3.7, 3.3.8, 4.1.2

=== 1.3.6
**Intent.** Make the purpose of user interface components, icons and regions programmatically determinable, so user agents can adapt them — for example by loading symbols or simpler terms familiar to the user, or by hiding regions the user does not need.

**Purpose vs. role.** 4.1.2 requires the role — what an element *is* (a link, a button). 1.3.6 adds the purpose — what it *represents* (a link to the home page, a search button, a help icon). This lets a tool replace an unfamiliar icon or label with one the user knows.

**How it can be met today.**
- **Regions:** ARIA landmarks or HTML sectioning elements (`<main>`, `<nav>`, `<header>`, `<footer>`, `<aside>`, `<search>`), so users can jump to, highlight or hide regions.
- **Inputs:** `autocomplete` tokens (as in 1.3.5).
- **Components and icons:** semantic metadata vocabularies such as WAI-Adapt, as user agent support matures.

**Why it matters for symbol users.** Non-vocal people often communicate with symbol sets that are proprietary and not interoperable. Mapping page elements to standard purposes lets a user agent show the user's own symbols on any site.

**Who benefits.** People with cognitive disabilities affecting memory, attention, language and executive function; people who use AAC symbols; users who want fewer features or a simplified interface.

**Examples.** A site with landmarks where users can hide everything except `main`; navigation links marked up so users can add their own icons; icons marked up so users can swap in a familiar icon set.

**Common failures.** Pages without landmarks or with every region as a generic `<div>`; icons with no programmatic purpose; custom controls whose meaning is conveyed only by an image.

**Related.** 1.3.1, 1.3.5, 4.1.2

=== 1.4.1
**Intent.** Ensure that sighted users who cannot distinguish some colours can still get information that is conveyed by colour differences — where each colour has a meaning assigned to it. The criterion requires a *visible* alternative to colour; it is about sighted users, not assistive technology.

**What colour can be used for — and needs a second cue.**
- **Conveying information:** "required fields are red", "Mary's sales in red, Tom's in blue" in a chart.
- **Indicating an action or state:** colour shows that a link opens a new window, or that a record saved successfully.
- **Prompting a response:** highlighting an empty required field.
- **Distinguishing an element:** links within body text distinguished from surrounding text only by colour.

**What counts as a second visual cue.** Text, an icon with a text alternative, a pattern or texture, shape, underline, position, or a border.
- **Lightness difference:** colours that differ in hue *and* in lightness, with at least **3:1** contrast between them, count as an additional cue. A light green and a dark red with 3:1 pass; inverting foreground and background also passes.
- **But** if the user must recognise *which* colour it is (green = valid, red = invalid outline), a non-colour indicator is required regardless of contrast.

**Links in body text.** A link distinguished from surrounding text only by colour needs 3:1 contrast against the text **and** an extra cue on hover and focus (e.g. underline) — or simply an underline at all times. A link styled identically to plain text does not fail this criterion (no colour is used), though it is poor usability.

**What it does not cover.**
- Visited vs unvisited link colours: browsers restrict `:visited` styling to colour for privacy, so this is not an author responsibility.
- Exposing information to screen readers: that is 1.1.1, 1.3.1 and 4.1.2. Conversely, making colour information available to assistive technology does not pass this criterion on its own.
- Colour used purely decoratively.

**Who benefits.** People with colour vision deficiency, people with partial sight, older users, users of monochrome or limited-colour displays, and people in poor lighting.

**Common failures.** Form errors shown only by a red border; required fields indicated only by red labels; charts and maps where series are distinguished only by hue; links in paragraphs with no underline and less than 3:1 contrast to text; status shown only as green/red dots.

**Related.** 1.3.1, 1.3.3, 1.4.3, 1.4.11

=== 1.4.2
**Intent.** Let people stop or turn down audio that starts automatically, because it makes it hard for screen reader users to hear their speech output — especially when the screen reader shares the system volume — and distracts others.

**What is required.** If audio plays automatically for more than 3 seconds, provide at least one:
- a mechanism to **pause or stop** the audio, or
- a mechanism to **control its volume independently** of the system volume (including down to zero).
Muting the whole computer is not a solution: it also mutes the screen reader.

**What "plays automatically" means.** Audio not started as a direct result of an intentional user action. Pressing a clearly labelled "Play" button, or a link that says it starts an audio experience, is not automatic. Two-way voice communication (conference calls) is not in scope, though independent volume control is good practice.

**Placement and best practice.**
- Put the control at the very start of the page, so it is found before the audio drowns out navigation.
- Better still: do not autoplay. Let users start sound, rather than requiring them to stop it.
- Audio shorter than 3 seconds is allowed.

**Non-interference.** This criterion applies to all content on a page, even content not relied upon for conformance — autoplaying audio anywhere on the page can block use of the whole page.

**Who benefits.** Screen reader users (especially those who are hard of hearing), people who have difficulty concentrating on text when sound plays.

**Common failures.** Background music or a promo video with sound that starts on load with no stop button; a stop control placed at the end of the page; a player whose only control is the system volume.

**Related.** 1.4.7, 2.2.2

=== 1.4.3
**Intent.** Provide enough contrast between text and its background so that people with moderately low vision or reduced contrast sensitivity can read it without contrast-enhancing assistive technology.

**The thresholds.**
- **4.5:1** for normal text; **3:1** for large text.
- **Large text** = at least 18pt (≈ 24 CSS px) regular, or 14pt (≈ 18.5 CSS px) bold. Very thin or unusual fonts may need more.
- Ratios are thresholds and are not rounded: 4.499:1 fails.
- Contrast is calculated from relative luminance, so hue is not a factor. This also accommodates colour vision deficiency.

**Why these numbers.** 3:1 is the ISO/ANSI minimum for normal vision. Vision of 20/40 (typical around age 80) brings a contrast sensitivity loss of about 1.5×, so 3 × 1.5 = 4.5:1. For 20/80, about 7:1 — used in 1.4.6.

**What text it applies to.** All text and images of text, including placeholder text, text in buttons, text shown on hover or focus, and text over images or gradients (measure against the least favourable part of the background).

**Exceptions (no requirement).**
- **Incidental:** text in inactive (disabled) controls; pure decoration (random words as a background pattern); text not visible to anyone; text that is part of a picture with significant other visual content (a street sign in a photo).
- **Logotypes:** text that is part of a logo or brand name. Wider brand guidelines (brand colours for headings, buttons) are not exempt.

**How to measure.**
- Use the colours from CSS or the user agent, not the rendered pixels — anti-aliasing makes thin fonts look fainter. If a font renders much fainter than its colour, use a heavier font or exceed the minimum.
- Font size in points comes from the user agent (1pt = 1.333px).
- Allowing users to switch to a low-contrast theme is fine, provided there is a way back to compliant colours.

**Who benefits.** People with low vision, reduced contrast sensitivity, colour vision deficiency, older users; everyone on a phone in sunlight.

**Common failures.** Light grey body text (#999 on white is 2.8:1); placeholder text used instead of a label at low contrast; white text on brand-orange buttons; text over photos without an overlay; low-contrast text on hover or focus states.

**Related.** 1.4.6, 1.4.11, 1.4.1, 1.4.5

=== 1.4.4
**Intent.** Ensure that text — including text in controls and labels — can be enlarged to 200% so people with milder visual impairments can read it without assistive technology such as a screen magnifier.

**Who does what.** Scaling is primarily the user agent's job: full-page zoom, text-only zoom, minimum font size settings. The author's job is to not break it. If the technology's user agents offer no scaling, the author must provide it (e.g. size controls on the page).

**What "without loss of content or functionality" means.**
- Text does not get clipped, truncated or cut off in fixed-size containers.
- Text does not overlap other text or controls.
- All controls remain visible and operable.
- This must hold at intermediate steps between 100% and 200%, not just at 200%.
- Met if at least one scaling mechanism supported by user agents works (usually browser zoom).

**Allowed truncation.** Components like an email subject column or spreadsheet cell may truncate long text, as long as the full content is available on focus or activation and there is an indication that it is truncated.

**Responsive layouts.** At high zoom, a media query may switch to a smaller font size for narrow layouts. That is fine, as long as text can still reach twice its default size in some way.

**Exclusions.** Captions and images of text; text controlled by the browser or platform (native `title` tooltips, the file picker dialog).

**Who benefits.** People with low vision who need larger text but do not use magnifiers; older users.

**Common failures.** Containers with fixed heights in px that clip text; text in `vw` units that does not grow with zoom; overlapping text at 200%; disabling zoom with `user-scalable=no` or `maximum-scale=1` in the viewport meta tag; important text rendered as images.

**Related.** 1.4.5, 1.4.8, 1.4.10, 1.4.12

=== 1.4.5
**Intent.** When the technology can achieve the visual look with real text, use text rather than images of text, so that people who need a particular presentation — font size, colours, font family, spacing, alignment — can adjust it.

**What is an image of text.** Text rendered into pixels and stored as an image, used instead of real text to achieve a particular look. Not included: text inside pictures with significant other visual content — graphs, screenshots, diagrams, photos.

**When images of text are allowed.**
- **Customizable:** the user can adjust the image's font, size and colours (e.g. images generated server-side from user settings).
- **Essential:** a particular presentation is essential to the information: logotypes, font samples, a historical letter shown as written.
- Symbolic characters on buttons ("B", "I", "ABC" for spellcheck) can be images, with text alternatives.
- The technology cannot achieve the look reliably, or doing so would break another criterion (e.g. 1.4.4).
- **Used in addition to** the same text shown to the user: e.g. an event poster image with its text also published next to it.

**Why it matters.** Images of text pixelate when enlarged, cannot be restyled with user stylesheets or reading tools, ignore text spacing and contrast settings, and cannot be translated or reflowed.

**Modern technologies make most images of text unnecessary.** Web fonts, CSS effects (shadows, gradients, rotation) and SVG text can replicate most designs.

**Relationship to 1.4.9.** 1.4.9 (AAA) removes the "customizable" and technical exceptions and applies even when text is also present.

**Who benefits.** People with low vision, people with visual tracking problems who change spacing and alignment, and people with reading disabilities who restyle text.

**Common failures.** Headings, buttons or navigation exported as images; banners with promotional text baked into a JPG with no text version; scanned PDFs or images of documents instead of real text; quotes rendered as images for style.

**Related.** 1.1.1, 1.4.4, 1.4.9, 1.4.12

=== 1.4.6
**Intent.** Provide stronger contrast between text and its background for people with more significant low vision who do not use contrast-enhancing assistive technology.

**The thresholds.**
- **7:1** for normal text; **4.5:1** for large text (18pt / 24px, or 14pt / 18.5px bold).
- Same calculation (relative luminance), same treatment of thresholds (not rounded) and same exceptions as 1.4.3: inactive components, pure decoration, invisible text, text in pictures with significant other content, logotypes.

**Why 7:1.** It compensates for the contrast sensitivity loss typical of 20/80 vision. People with greater vision loss usually use assistive technology with its own contrast enhancement and magnification.

**Practical implications.** Body text usually needs near-black on white (or the reverse). Mid-grey text that passes 4.5:1 often fails 7:1. Brand colour palettes may need darker variants for text.

**Who benefits.** People with low vision (around 20/80), people with reduced contrast sensitivity, older users, people with colour vision deficiency.

**Common failures.** Grey secondary text that passes AA but not AAA; coloured links that pass 4.5:1 but not 7:1; text on tinted backgrounds.

**Related.** 1.4.3, 1.4.8, 1.4.11

=== 1.4.7
**Intent.** Keep non-speech sounds low enough that people who are hard of hearing can separate speech from background sound or noise.

**Scope — all three conditions must hold.**
- Prerecorded **audio-only** content (not video).
- Contains **primarily speech** in the foreground (podcasts, narrations, lectures, audiobooks).
- Is **not** an audio CAPTCHA, an audio logo, or vocalisation that is primarily musical (singing, rapping).

**Ways to meet it — at least one.**
- **No background:** the recording has no background sounds.
- **Turn off:** the user can switch background sounds off (e.g. a separate music track with its own control).
- **20 dB rule:** background sounds are at least 20 dB quieter than the speech — roughly four times quieter. Occasional sounds lasting one or two seconds are allowed.

**Why 20 dB.** The value comes from research on assistive listening systems and hearing aid interference: below this level, background noise significantly reduces speech intelligibility for hard-of-hearing listeners.

**Practical tips.** Mix narration well above music beds; avoid continuous ambient noise under speech; when producing, keep speech and music on separate tracks so a version without music can be published.

**Who benefits.** People who are hard of hearing and hearing aid users; also non-native listeners and anyone in noisy environments.

**Common failures.** A podcast intro with loud music under the host's voice throughout; narration over continuous sound effects or ambient noise; no way to turn off background music.

**Related.** 1.4.2, 1.2.1

=== 1.4.8
**Intent.** Present blocks of text so that layout does not interfere with readability, and let users adjust the presentation they need. The requirement is that a **mechanism** exists — it can be the browser or another user agent; content does not have to use these values or build its own controls.

**The five aspects a mechanism must make achievable.**
- **Colours:** users can select foreground and background colours. Some people need very specific — even low-contrast — combinations.
- **Line width:** no more than 80 characters or glyphs (40 for CJK, whose characters are about twice as wide). Long lines make it hard to find the start of the next line.
- **No full justification:** text is not aligned to both margins. Justification creates uneven word spacing and "rivers" of white that make reading hard, especially for people with dyslexia.
- **Spacing:** line spacing at least 1.5 within paragraphs; paragraph spacing at least 1.5 times the line spacing (i.e. a blank line of 150% between paragraphs).
- **Resizing:** text can be enlarged to 200% without horizontal scrolling to read a line, in a maximised window on a typical desktop.

**Clarifications.**
- Applies to blocks of text (more than one sentence), not to short labels.
- Two equal columns pass the scrolling requirement: at 200% you read one column vertically, then scroll once to the other.
- Very long words or URLs that run off-screen do not fail it.
- Writing systems that do not use one of these aspects can ignore it.

**Who benefits.** People with cognitive, language and learning disabilities (including dyslexia) who lose their place, and low-vision users.

**Common failures.** Fully justified body text; text columns spanning the full width of wide screens with no maximum width; colours that cannot be overridden because they are set inline with `!important` or embedded in images; fixed-width layouts that need horizontal scrolling at 200%.

**Related.** 1.4.4, 1.4.6, 1.4.10, 1.4.12

=== 1.4.9
**Intent.** Enable people who require a particular visual presentation of text to adjust it, by implementing all text as real text that can be restyled — images of text only where decoration or an essential presentation requires it.

**Only two situations allow images of text.**
- **Pure decoration:** the text conveys no information.
- **Essential presentation:** information would be lost without that particular look — logotypes, a font specimen, a historical letter shown as written. Symbolic characters on buttons ("B", "I", "ABC") can also be images, with text alternatives.

**Difference from 1.4.5.** 1.4.5 (AA) also allows images of text that the user can customise, those where the technology cannot achieve the look, and those that duplicate text shown next to them. 1.4.9 removes all of these: if the text is informative and its look is not essential, it must be real text.

**Not affected.** Text in pictures that contain significant other visual content — charts, screenshots, diagrams, photos — is not an image of text.

**Who benefits.** People with low vision who change font size, family or colours; people with visual tracking problems who change spacing or alignment; people with reading disabilities.

**Common failures.** Styled quotes, headings, banners or navigation rendered as images; text in infographics that is purely textual; images of text with the same text alongside (passes 1.4.5, fails 1.4.9).

**Related.** 1.4.5, 1.1.1, 1.4.8

=== 1.4.10
**Intent.** Let users enlarge content without having to scroll in two dimensions to read. When lines run off the edge of the viewport, users must scroll back and forth for every line, lose their place, and expend much more effort.

**The size targets.**
- Vertically scrolling content (most languages): usable at **320 CSS px** wide — equal to a 1280 px window zoomed to 400%.
- Horizontally scrolling content (vertical scripts): usable at **256 CSS px** high.
- 400% refers to each dimension, not area. Actual viewports vary (browser chrome, scrollbars, split screens); what matters is that content *can* work at that size.

**What reflow allows.**
- Responsive changes are fine: stacking into one column, collapsing navigation into a menu button, moving or simplifying components. Relocating content is not a loss of information, as long as it remains reachable.
- Not everything must stack: a carousel can scroll horizontally if each panel fits 320 px; a side-by-side diff can scroll horizontally if each column fits 320 px.

**Exception: content that needs two-dimensional layout.** Data tables and grids, maps, diagrams and images needed for understanding, video, games, presentations and slides, interfaces with toolbars that must stay in view (editors), code or nested lists where indentation carries meaning, fixed-size documents in editing tools.
- The exception covers **only that section**. A table may scroll in its own container, but the heading, paragraphs, search and pagination around it must still reflow. Cells within a table should also reflow.
- Best practice: give excepted content its own scrolling container (e.g. `overflow: auto`) and use `max-width: 100%` on images and video, so the whole page does not scroll sideways.

**Truncation.** Long strings that are truncated must be available in full by some mechanism (a link, expand control, or on focus).

**Overlaps.** At high zoom, sticky headers, footers, cookie banners and fixed ads can cover most of the screen and hide focus (2.4.11); make them static or dismissible at small sizes. Reflow does not itself require text to grow (that is 1.4.4).

**Who benefits.** People with low vision who zoom to 200–400%, people using small screens or split windows.

**Common failures.** Fixed-width layouts (`width: 1200px`); text containers that do not wrap (`white-space: nowrap`); content cut off or hidden behind overlapping fixed elements at 400%; whole-page horizontal scrolling caused by a table or image that could be contained; navigation that disappears with no menu button.

**Related.** 1.4.4, 1.4.12, 1.3.4, 2.4.11

=== 1.4.11
**Intent.** Ensure that user interface components and graphics needed for understanding can be perceived by people with moderately low vision. The 3:1 threshold mirrors the one for large text in 1.4.3.

**User interface components — what needs 3:1 against adjacent colours.**
- **Visual information needed to identify a control:** the border of a text input when that is the only indication it is a field, the outline of a checkbox, an icon-only button's icon, the down-arrow of a select.
- **Visual information needed to identify a state:** the check mark, the filled radio dot, the position of a toggle, the focus indicator, a selected-tab indicator.
- **Boundaries are not always required:** a button identified by its text, position or context does not need a contrasting border. A boundary is required only if nothing else shows the control exists.
- **"Adjacent colours":** for an input with a white interior, dark border and white page, the relevant contrast is the border against the outside. Decorative borders or shadows that do not help identify the control can be ignored.
- **Not required:** contrast *between* states of the same component (e.g. hover vs default, visited vs unvisited); author hover effects where the pointer itself shows hover — as long as the component does not lose contrast.
- **Focus indicators:** an author-styled indicator must reach 3:1 against the colours it sits next to (outside, inside, or both, depending on where it is drawn). Browser default focus styles are exempt.

**Graphical objects — what needs 3:1.**
- Parts of graphics required to understand the content: stand-alone icons without text, lines in a line chart, slices of a pie chart, key shapes in an infographic.
- Test the least-contrasting area: if you imagine that area invisible, can you still understand the graphic? If yes, it passes.
- **Not required** when: the same information is in text (labels *and* values on the chart, or a data table); the graphic is decorative; it is a logo; or a particular presentation is **essential** (flags, photos, screenshots, heat maps, medical diagrams with natural colours).
- Logos styled low-contrast by author choice (e.g. greyed until hover) are not essential and must comply.

**Exclusions.** Inactive (disabled) components; components whose appearance is entirely determined by the browser and not modified.

**Measuring.** Use CSS colour values; thresholds are not rounded (2.999:1 fails); thin lines may render fainter than their colour, so prefer thicker strokes.

**Who benefits.** People with low vision and reduced contrast sensitivity, including those with colour vision deficiency.

**Common failures.** Light grey input borders (#ccc, 1.6:1) as the only indication of a field; pale checkbox outlines (#9d9d9d, 2.7:1); author-styled focus rings below 3:1; icon-only buttons in pastel colours; chart lines and pie slices that cannot be told apart and have no labels or values.

**Related.** 1.4.1, 1.4.3, 2.4.7, 2.4.13

=== 1.4.12
**Intent.** Ensure that when people override text spacing to make reading easier, content remains readable and operable. Content does not have to use these values; it must not break when the user applies them.

**The test values — applied together, changing nothing else.**
- Line height: **1.5 ×** font size.
- Spacing after paragraphs: **2 ×** font size.
- Letter spacing: **0.12 ×** font size.
- Word spacing: **0.16 ×** font size.
A bookmarklet or user stylesheet applying these is the usual test.

**What counts as loss of content or functionality.**
- Text cut off vertically or horizontally in fixed-size boxes (headings, buttons, cards, tabs).
- Text overlapping other text or controls.
- Controls becoming hidden or unusable.

**Ellipses are acceptable** when truncation appears as a result of spacing, provided the full text remains available — revealed on focus or activation, or on the page a link leads to. Truncation with no way to see the full text fails.

**Responsibilities.**
- Author: do not prevent overrides (e.g. inline `!important` that blocks user styles) and let containers grow with their content.
- User: chooses the tool and values; spacing beyond these values is at the user's discretion. Content does not fail if the user's tool itself fails to apply the styles.

**Scope.** Applies to content implemented in markup languages that support these properties (HTML/CSS). Not to images of text, captions burned into video, or text drawn in `<canvas>` (treated as images of text). Languages that do not use a property (e.g. paragraph spacing in Japanese) can ignore it.

**Who benefits.** People with low vision and people with dyslexia who increase spacing to read faster; adaptable spacing also makes other user styles (e.g. wider fonts) more likely to work.

**Common failures.** Fixed `height` on text containers; buttons and tabs with fixed widths that clip labels; headings that overlap following text; `overflow: hidden` on cards hiding the end of the text.

**Related.** 1.4.4, 1.4.8, 1.4.10

=== 1.4.13
**Intent.** When additional content appears on pointer hover or keyboard focus and disappears when it is removed — custom tooltips, sub-menus, non-modal popups — design it so users can perceive the content and dismiss it without disrupting their work. Such content often appears unintentionally, goes unnoticed, or covers what the user is doing.

**The three conditions.**
- **Dismissible:** users can hide it without moving the pointer or focus, typically with **Esc**. Particularly important for screen magnifier users, whose magnified view follows the pointer and may be covered entirely.
    - Not required if the content reports an input error, or if it does not obscure or replace other meaningful content (it appears over empty space).
- **Hoverable:** if it appears on hover, the pointer can move onto it without it disappearing. Magnifier users may need to pan across it; users with large cursors need to move off the trigger to read it. This implies the content is adjacent to or overlaps the trigger.
- **Persistent:** it stays visible until the user removes hover/focus, dismisses it, or the information is no longer valid (e.g. a "busy" message). No timeouts that hide it on their own.

**Scope.**
- Covered: custom tooltips, hover cards, mega-menus and sub-menus, non-modal popups that appear on hover or focus.
- Not covered: browser-native tooltips from the `title` attribute; content shown on click or activation; modal dialogs (they must take focus and should not open on hover — see 3.2.1); elements that become visible themselves on focus without adding content, like skip links.
- Content shown on hover should also be available on keyboard focus (2.1.1).

**Who benefits.** Screen magnifier users, people using large pointers, people with low vision or cognitive disabilities who need more time, people with low pointer accuracy who trigger content accidentally.

**Common failures.** Tooltips that disappear when the pointer moves toward them; hover content that cannot be closed with Esc and covers the next control; tooltips that vanish after a few seconds; sub-menus that close on a small pointer movement.

**Related.** 2.1.1, 3.2.1, 2.4.11, 4.1.2

=== 2.1.1
**Intent.** Ensure that, wherever possible, all functionality can be operated through a keyboard interface — so it works for people who cannot use a mouse and for the many assistive technologies that emulate a keyboard: speech input, switch and sip-and-puff systems, on-screen keyboards, scanning software.

**What "keyboard operable" means in practice.**
- Every function reachable and usable with the keyboard: moving focus (Tab, arrow keys), activating (Enter, Space), selecting, moving, resizing.
- **No specific timings:** users must not need to press keys in quick succession or hold a key down for a long time.
- Following platform conventions (Enter and Space on buttons, arrows in menus) is best practice, but not required. A custom button that only reacts to Enter still passes.
- Not every pointer-operable element must itself be focusable — what matters is that keyboard users can perform the **same or comparable action**. Example: a search button that is not focusable passes if Enter in the search field submits the form. A separate keyboard mode also passes, though users must be able to discover it.
- Content must keep working with operating system keyboard features such as sticky or locked modifier keys.

**The path-dependent exception — narrower than it seems.**
- Exempt only when the *underlying function* needs input that depends on the path of movement, not just endpoints: freehand drawing, watercolour painting where speed and pressure matter, a flight simulator teaching real-time control.
- **Not exempt:** drag and drop to a location, drawing straight lines or regular shapes, resizing, moving objects, connecting dots. These need keyboard alternatives (cut/paste, move buttons, arrow-key movement).
- The exception is about the function, not the input technique: handwriting is path-based, but text entry is not.

**MouseKeys does not count.** It makes the keyboard emulate a mouse; the content must be operable through keyboard events.

**Who benefits.** Blind users, people with motor disabilities or tremor, users of speech input, switches and other keyboard emulators, people with low vision who struggle to track a pointer.

**Common failures.** Clickable `<div>` or `<span>` elements without `tabindex` and key handlers; functions triggered only on `mouseover` or `dblclick`; drag-and-drop interfaces with no alternative; custom selects, sliders or menus that ignore arrow keys; elements removed from the tab order with `tabindex="-1"` with no other way to reach the function.

**Related.** 2.1.2, 2.1.3, 2.1.4, 2.4.3, 2.4.7, 2.5.7

=== 2.1.2
**Intent.** Ensure keyboard focus never gets stuck inside part of a page. If focus can move into a component with the keyboard, it must be able to leave it with the keyboard alone. People relying on the keyboard often have no other way out — a trap can make the whole page unusable.

**When focus counts as trapped.**
- Not trapped: the user can leave with unmodified Tab, Shift+Tab, arrow keys, or another **standard exit method**. Esc is the usual standard exit; what counts as standard depends on platform and user agent.
- Still passes: leaving requires a non-standard key combination, **provided the user is told how** — before the component and/or inside it.
- Trapped: no keyboard way out, or a non-standard way that is not explained.

**Deliberate focus containment is allowed.** Modal dialogs and popovers may keep Tab cycling inside them, as long as the user can close them by keyboard (Esc, a Close button) and return to the page.

**Typical sources of traps.** Embedded third-party content and plugins (players, maps, iframes, legacy applets), rich text editors where Tab inserts indentation, custom widgets that capture all key events, focus-management scripts that keep sending focus back.

**Example of a pass with instructions.** In a rich text editor, Tab indents text; when the editing area gets focus, a message says "Press Alt+F10 to move to the toolbar".

**Non-interference.** This applies to all content on the page, including content not relied upon for conformance.

**Who benefits.** Keyboard-only users, screen reader users, switch users, people with motor disabilities.

**Common failures.** An embedded video player or map that captures Tab with no exit; an editor where Tab inserts characters and no exit is documented; a modal that cannot be closed by keyboard; a script that returns focus to a field until it is valid.

**Related.** 2.1.1, 2.4.3

=== 2.1.3
**Intent.** Ensure that **all** content is operable from the keyboard, without the path-dependent exception allowed in 2.1.1.

**What changes compared with 2.1.1.**
- No exception for functions that depend on the path of movement. This does not mean freehand drawing must somehow be made keyboard accessible — it means content requiring path-dependent input **cannot conform** to Guideline 2.1 at AAA.
- Everything else is the same: no specific timings for keystrokes; platform conventions are best practice, not required; comparable keyboard actions or a separate keyboard mode are acceptable.

**Practical implications.** Drawing and design tools need keyboard methods to create and edit shapes; games need keyboard controls for every action; signature fields need an alternative such as typing a name.

**Who benefits.** People who can only use a keyboard or keyboard emulator (switches, speech input, sip-and-puff).

**Common failures.** Any function available only by pointer, including freehand drawing or gesture-based features without a keyboard alternative.

**Related.** 2.1.1, 2.5.1

=== 2.1.4
**Intent.** Reduce accidental activation of keyboard shortcuts that use only printable characters. They help many keyboard users, but are disastrous for speech input users — whose dictated words become strings of letters — and for keyboard users who hit keys by accident.

**Why speech users are affected.** Speech users work in a mixed mode of dictation and commands. If focus is on a page with single-key shortcuts, a stray phrase becomes a burst of commands. Example: in webmail with shortcuts Y (archive), K (next), M (mute), a colleague saying "Hey Kim" archives a message, moves down and mutes a thread. Shortcuts that need a modifier key are not triggered this way.

**What is covered.**
- Shortcuts made of letters (any case), punctuation, numbers or symbols — regardless of how many physical keys a character needs ("?" via Shift+/, "é" via AltGr+E).
- Sequences of character keys, e.g. G then A.

**What is required — at least one.**
- **Turn off:** a mechanism to disable the shortcuts.
- **Remap:** a mechanism to change them to include a non-printable key (Ctrl, Alt, etc.).
- **Active only on focus:** the shortcut works only when its component has focus.

**Not affected.**
- Typing a letter to jump to an option in a focused listbox or menu.
- Menus opened with a modifier first (Alt, Alt+F) and then a letter.
- Access keys, which normally use modifiers.

**Who benefits.** Speech input users; keyboard users with tremor or limited dexterity; people with cognitive disabilities, if all shortcuts can be remapped to match other applications.

**Common failures.** Web apps (mail, chat, document editors, video players) with global single-letter shortcuts and no setting to turn them off or change them; "/" or "S" jumping to search from anywhere on the page with no way to disable it.

**Related.** 2.1.1, 2.5.3, 3.2.1

=== 2.2.1
**Intent.** Give people with disabilities enough time to read and use content. Blind and low-vision users, people with dexterity impairments, cognitive or language limitations, and deaf users reading in a second language often need more time than expected.

**What counts as a time limit.** Any process that happens without user initiation after a set time or periodically: session timeouts, auto-refresh or redirects after a delay, content that disappears, a window to respond to a prompt, and content that moves or advances faster than people can read it.

**Options, in order of preference — at least one.**
1. **Turn off** the limit before encountering it.
2. **Adjust** it before encountering it, over a range of at least **10×** the default.
3. **Extend:** warn before time expires, give at least **20 seconds** to extend with a simple action ("press any key", a button), and allow at least **10** extensions.

**Why these numbers.** 10× comes from clinical experience: if 15 seconds is the default, 150 seconds lets almost anyone respond. 20 seconds to hit any switch is enough for almost all users, while not leaving kiosks open indefinitely. 20 hours exceeds a waking day.

**Exceptions.**
- **Real-time events** where no alternative is possible (an auction deadline that applies to everyone).
- **Essential limits** where extending would invalidate the activity (ticket holds before seats return to sale; timed exams — though a third party may grant extra time). Time-based one-time codes for security can be essential.
- **Longer than 20 hours.**

**When it does not apply.**
- Content where the information is available another way: a 5-second toast about new mail is fine if the inbox shows the same.
- Repeating or user-controllable moving content (carousels, scrolling text) — handled by 2.2.2.
- Limits outside the author's control (browser, network). Server-side and security timeouts set by the site are covered.
- Instant redirects (HTTP 3xx) are not timed.

**Good practice.** Move as much of a process as possible out of the time-critical part (e.g. collect details before the ticket hold starts).

**Who benefits.** People with physical, visual, cognitive and language disabilities, screen reader users, deaf users working through interpreters.

**Common failures.** Sessions that expire without warning and lose data; `<meta http-equiv="refresh">` timed redirects or reloads; auto-advancing slides or messages that disappear before they can be read; extension warnings that give less than 20 seconds or cannot be operated by keyboard.

**Related.** 2.2.2, 2.2.3, 2.2.5, 2.2.6, 3.2.1

=== 2.2.2
**Intent.** Avoid distracting users with moving, blinking, scrolling or auto-updating content that runs alongside what they are trying to read or do. Movement is a barrier for people with attention disorders, people who read slowly or have trouble tracking moving objects, and screen reader users.

**Two categories.**
- **Moving, blinking, scrolling** — content that conveys a sense of motion: carousels, animations, marquees, tickers, background video, animated GIFs. A mechanism to pause, stop or hide is needed if it (1) starts automatically, (2) lasts more than **5 seconds**, and (3) is shown in parallel with other content.
- **Auto-updating** — content that changes at preset intervals: live news, weather, stock prices, auto-advancing messages. A mechanism to pause, stop, hide **or control the update frequency** is needed if it starts automatically and is shown in parallel. There is no 5-second allowance.

**What "starts automatically" means.** Not the direct result of an intentional activation like pressing a button. Movement triggered indirectly — on hover, focus, or scrolling into view — also counts as automatic (and may also fail 2.3.3).

**What counts as a valid mechanism.**
- A real control — typically a pause button — that does not tie up the user. Pausing only while the element has focus or hover, then restarting, does not count.
- After pausing, content may resume where it stopped (best for things to read) or jump to the current state (best for real-time data like a stock ticker or weather radar). Hiding has the same effect as jumping to current.
- Best practice: one control that pauses all moving content on the page.

**Exceptions and out-of-scope cases.**
- Movement **essential** to the activity (e.g. a progress animation when no interaction is possible).
- Content **not presented in parallel** with other content: a preloader that is the only thing on screen, a mandatory full-page ad.
- Blinking that stops within 5 seconds.
- Flashing that can cause seizures is a separate matter (2.3.1).

**Non-interference.** Applies to all content on the page, even content not relied upon for conformance.

**Who benefits.** People with ADHD and other attention disorders, people with reading, intellectual or low-literacy disabilities, people with low vision or tracking difficulties, screen reader users.

**Common failures.** Auto-rotating carousels without a pause button; scrolling news tickers; looping background videos without controls; animated banners and GIFs that loop forever; live feeds that update continuously with no way to pause.

**Related.** 2.2.1, 2.3.1, 2.3.3, 1.4.2

=== 2.2.3
**Intent.** Minimise content that requires timed interaction, so people who are blind, have low vision, cognitive limitations or motor impairments can use it at their own pace.

**What is required.** Timing is not an essential part of the activity. Unlike 2.2.1, there is no option to merely make limits adjustable or extendable — the activity should be designed without them.

**The only exceptions.**
- **Non-interactive synchronized media** — a video naturally plays in time.
- **Real-time events** — a live auction, a live multiplayer event.
Notably, the "essential" and "20 hours" exceptions of 2.2.1 do not apply here.

**How to design without timing.**
- Tests scored on answers rather than speed, calibrated without time limits.
- Turn-based rather than real-time games, so either player can pause.
- Processes without session timeouts, or with saved progress.

**Who benefits.** People with physical disabilities who type or react slowly, people with low vision and screen reader users who need time to find and read things, people with cognitive or language limitations, deaf users reading in a second language.

**Common failures.** Timed quizzes; forms or checkouts with countdowns; games that require fast reactions when timing is not essential to their purpose.

**Related.** 2.2.1, 2.2.4

=== 2.2.4
**Intent.** Let users postpone or suppress interruptions from the author or server, so people with attention disorders or cognitive limitations can focus, and screen reader and low-vision users can keep their reading position.

**What counts as an interruption.** Content updates, alerts, pop-ups, notifications, chat invitations, promotional overlays, and content refreshing while the user is reading it — anything initiated by the site rather than the user.

**What is required.** A way to postpone or turn them off, e.g. a preference to hold all updates until the end of the session, or to receive them only on request.

**The emergency exception.** Interruptions about emergencies may always be delivered: civil emergency alerts, danger to health, safety or property, and warnings about data loss or loss of connection.

**Why it matters for screen readers.** If content updates while it is being read, a user may start reading one topic and finish in another, without realising the content changed.

**Who benefits.** People with attention deficit disorders, people with cognitive limitations, screen reader and screen magnifier users.

**Common failures.** Newsletter or chat pop-ups that appear repeatedly and cannot be turned off; live updates that re-render the article being read; notifications that cannot be paused.

**Related.** 2.2.2, 4.1.3, 3.2.5

=== 2.2.5
**Intent.** Let users complete authenticated processes even if their session ends, without losing what they already entered. People with disabilities often need longer, and are more likely to hit inactivity timeouts.

**What is required.** When an authenticated session expires — through inactivity, a login from another device, or a security check — the user can re-authenticate and continue the activity **without loss of data**.

**How it is done.**
- Store submitted data server-side even after the session times out, and restore the user to the same step after login.
- Offer re-authentication in a new window or dialog so the work in progress stays intact.
- Save drafts automatically.

**Examples.** A checkout restored at the same stage with the same details after logging in again; an email client that prompts before timeout and lets the user re-authenticate in a new window, then send the unfinished message.

**Relationship to other criteria.** Session time limits remain subject to 2.2.1 (warn and allow extension); 2.2.6 adds warning users about inactivity that loses data.

**Who benefits.** People with cognitive limitations who read slowly, screen reader users navigating complex forms, people with motor impairments or using alternative input devices.

**Common failures.** Logging back in returns the user to the start with an empty form; unsent messages or form data discarded on timeout.

**Related.** 2.2.1, 2.2.6, 3.3.7

=== 2.2.6
**Intent.** Ensure users know how long they can be inactive before a timeout causes data loss, so they can plan, take breaks, or prepare information in advance. Long processes can overwhelm people with cognitive disabilities, who may need to stop and come back.

**What is required — one of:**
- **Preserve data for more than 20 hours** of inactivity (the preferred approach), or
- **Warn users** of the duration of inactivity that will cause data loss.

**How to warn.** State the timeout once, at the start of the task or process — not at every step. Example: "For security, this application times out after 60 minutes of inactivity."

**Scope.**
- Only timeouts within the provider's knowledge or control. Data lost because the user closed the browser does not fail.
- A form with no timeout at all passes.
- Privacy and security rules (e.g. PCI DSS, HIPAA) may restrict storing data, and may require consent before storing it; that is why warning is an acceptable alternative.

**Relationship to 2.2.1.** 2.2.1 deals with letting users turn off, adjust or extend limits; 2.2.6 specifically ensures users are told in advance about inactivity timeouts.

**Who benefits.** People with language, memory, attention and executive-function disabilities, and older users.

**Common failures.** Booking or application forms that discard data after inactivity with no prior notice; timeouts mentioned only in a last-second warning.

**Related.** 2.2.1, 2.2.5

=== 2.3.1
**Intent.** Let people use all content without it triggering seizures due to photosensitivity. People with photosensitive epilepsy can have a seizure from content that flashes at certain frequencies for more than a few flashes; saturated red flashing is especially dangerous. The criterion is based on broadcasting standards, adapted to closer screen viewing.

**The rule.** Nothing on the page flashes more than **three times in any one-second period** — unless the flashing is below both the **general flash threshold** and the **red flash threshold**.

**What makes a flash fall below threshold.**
- **Area:** the combined area flashing concurrently and contiguously is smaller than about 25% of a 10° visual field — defined as **341 × 256 CSS px (87,296 CSS px²)**, which represents the central vision most susceptible to stimuli. The same CSS size occupies a similar share of the visual field on phones and large screens.
- **Luminance (general flash):** a pair of opposing changes in relative luminance of 10% or more, where the darker state is below 0.80 relative luminance. For HDR or non-sRGB video: a change of 20 cd/m² or more where the darker image is below 160 cd/m² (ITU-R BT.1702).
- **Red flash:** a pair of opposing transitions involving a saturated red (R/(R+G+B) ≥ 0.8) with a chromaticity change above 0.2 in the CIE 1976 UCS diagram.

**How to evaluate.**
- Analyse at the largest size the content may be shown (e.g. full-screen video) and at standard zoom.
- Analyse looping clips (GIFs) while they loop.
- Use a tool such as the Photosensitive Epilepsy Analysis Tool (PEAT) or a Harding-based analyser for video.
- Only flashing caused by the content counts, not by displays or hardware.

**Flash vs. blink.** Blinking is a distraction problem (2.2.2) and may be allowed briefly. Flashing is a seizure risk and cannot be allowed even for a second, and a "stop" button is no remedy — a seizure can occur before it is used.

**Limitations.** Users closer to the screen, or using magnification, can still be affected by flashing that technically passes. Avoiding flashing altogether is safest.

**Non-interference.** Applies to all content on the page.

**Who benefits.** People with photosensitive epilepsy and other photosensitive seizure disorders; also people prone to migraines, dizziness or nausea from flashing.

**Common failures.** Full-screen strobe effects, rapid explosions, lightning or muzzle-flash sequences in video; flashing GIF banners; rapidly alternating high-contrast patterns or red/black transitions; "glitch" effects in hero animations.

**Related.** 2.3.2, 2.2.2, 2.3.3

=== 2.3.2
**Intent.** Further reduce the chance of seizures by eliminating **all** flashing faster than three times per second, regardless of size or brightness. Seizures cannot be eliminated entirely — some people are extremely sensitive — but this goes beyond the international broadcast thresholds used at Level A.

**Difference from 2.3.1.** 2.3.1 allows flashing that is small enough or dim enough. 2.3.2 has no thresholds: even a single flashing pixel fails. The intent is to guard against anything larger than a pixel, but since magnification and high-contrast settings are unknown, the rule bans all flashing above 3 per second.

**Flash vs. blink.** "Blink" means slow repeating changes that distract (2.2.2). "Flash" means changes that could cause a seizure. Blinking faster than three times per second is also a flash.

**How to comply.** Design without flashing elements; edit video so that bright flashes (lightning, camera flashes) occur no more than three times in any second; avoid rapidly flickering loading indicators and animated effects.

**Who benefits.** People with photosensitive seizure disorders, including the most sensitive.

**Common failures.** Any element or video segment flashing more than three times per second, even if small or low-contrast.

**Related.** 2.3.1, 2.2.2

=== 2.3.3
**Intent.** Let users prevent non-essential motion animation that is triggered by their own interaction. Such motion can cause distraction, dizziness, nausea and migraines — for people with vestibular (inner ear) disorders the reaction can be severe enough to require bed rest.

**What is covered.**
- **Motion animation** — something moving or appearing to move: parallax backgrounds, elements sliding, zooming, spinning or flying in as you scroll, page-flip or zoom transitions, scroll-jacking effects.
- **Triggered by interaction** — scrolling, clicking, hovering, focusing, swiping.
- Not covered: changes of colour, opacity or blur that do not create motion; the essential movement of scrolling itself (content moving into view as the user scrolls).

**Relationship to 2.2.2.** 2.2.2 covers animation the page starts **automatically**; 2.3.3 covers animation triggered **by the user's interaction**. Some animation (e.g. started when scrolled into view) can fail both.

**Ways to comply — any one.**
- Avoid non-essential motion in interactions.
- Provide a control (ideally site-wide) to turn off non-essential animation.
- Respect the user's operating system setting via the `prefers-reduced-motion` media query — remove or replace motion with a simple fade or instant change.

**The essential exception.** Motion essential to the function or information: previewing an animation in an animation editor, a demonstration of a physical process where motion is the content.

**Who benefits.** People with vestibular disorders, motion sensitivity, migraines, and attention or cognitive disabilities that make motion distracting.

**Common failures.** Parallax scrolling with no way to turn it off; scroll-triggered fly-in effects that ignore `prefers-reduced-motion`; large zoom or slide page transitions with no reduced-motion alternative; background elements that move when the pointer moves.

**Related.** 2.2.2, 2.3.1

=== 2.4.1
**Intent.** Give people who navigate sequentially — by keyboard, screen reader or switch — a direct way to reach the main content without going through blocks repeated on every page. A sighted mouse user just looks past the header and clicks; a keyboard user might need 40 Tab presses and a screen reader user might hear 200 words first.

**What counts as a repeated block.** Navigation menus, site headers, banners, advertising, sidebars, long lists of filters that come before results. Single repeated words, phrases or links are not blocks.

**Ways to provide a bypass mechanism.**
- **Skip link** as one of the first focusable elements ("Skip to main content"), which actually moves focus to the main content. It may be visually hidden until focused.
- **Landmarks:** `<main>`, `<nav>`, `<header>`, `<footer>` (or ARIA roles) let screen reader users jump between regions.
- **Headings** at the start of each section, so users can jump by heading.
- Collapsible navigation, or skip links before repeated blocks within long pages (e.g. "Skip filters").
Using landmarks or headings is a sufficient technique; a skip link additionally helps sighted keyboard users who have no landmark navigation.

**Clarifications.**
- Applies to blocks repeated across a set of related pages; for content repeated within one page, a skip mechanism is helpful but not required.
- Authors need not duplicate browser functions: if navigation sits at the bottom, browsers' "go to top" makes a skip link unnecessary.
- Structural markup on every page is strongly encouraged regardless (1.3.1).

**Who benefits.** Screen reader users, keyboard-only and switch users (for whom each keystroke can be slow or painful), screen magnifier users who must otherwise search for where content starts, and people with cognitive limitations.

**Common failures.** No skip link, landmarks or headings; a skip link whose target is not focusable, so focus does not move; a skip link hidden permanently (`display: none`); a skip link that only becomes visible in a place users cannot see.

**Related.** 1.3.1, 2.4.3, 2.4.6, 2.4.10

=== 2.4.2
**Intent.** Help users find content and orient themselves by giving each page a title that describes its topic or purpose. Titles identify the current location without users having to read the page, and appear in browser tabs, history, bookmarks and search results.

**What makes a title descriptive.**
- It identifies the specific page, not just the site: "Order confirmation – Bank XYZ", not just "Bank XYZ".
- For a document or web application, its name can be sufficient.
- It need not be long, but must be accurate and distinguishable from other pages.
- Best practice: put the unique part first, then the site name — "Contact us | Example Ltd" — so it is announced first and visible in narrow tabs.
- Best practice: match the title to the link or heading that led to the page.

**Dynamic titles.**
- In single page applications, update `document.title` when the view changes.
- In applications, include the state where helpful: "Bank XYZ, December 2025 statement for account 1234".
- In multi-step forms or search results, reflect the step or query (and errors, e.g. "Error: Delivery details – Checkout").

**Who benefits.** Screen reader users, who hear the title first on page load; people with visual impairments switching between many tabs; people with cognitive disabilities, limited short-term memory or reading disabilities; people with mobility impairments who navigate by audio.

**Common failures.** Missing `<title>`; generic titles like "Untitled document", "Home" or the site name on every page; titles not updated in single-page apps; titles that describe something else (left over from a template).

**Related.** 2.4.4, 2.4.6, 2.4.8, 3.2.4

=== 2.4.3
**Intent.** When people navigate sequentially (usually with Tab), they should encounter focusable elements in an order consistent with the meaning of the content and that lets them operate it. A logical order lets users build a consistent mental model; a random one disorients them.

**What a logical order means.**
- It preserves meaning and operability. More than one order may be valid — in a table, row by row or column by column are both acceptable; only one needs to be provided.
- It does not have to match the visual layout exactly, as long as the relationships implied by the layout are preserved. Independent columns may be visited in either order, though matching the visual reading order is best practice.
- Focus order may differ from the reading order (1.3.2), but must make sense both for screen reader users following the DOM and for sighted keyboard users following the visual page.
- Arrow-key navigation inside composite widgets (trees, menus, grids) is a separate model and not what this criterion assesses.

**Dynamic content and dialogs.**
- **Non-modal dialogs or disclosures:** insert their controls in the focus order right after the trigger.
- **Modal dialogs:** move focus into the dialog, make the rest of the page inert, and return focus to the trigger (or the next logical element) on close.
- Content added to the page should not leave focus behind or send it to the top of the page.

**Other pitfalls.**
- Positive `tabindex` values (1, 2, 3…) override the DOM order and almost always create jumps.
- CSS reordering (flexbox `order`, grid placement, absolute positioning) can make focus jump around visually.
- Nested focusable elements (`<div tabindex="0"><button>`) make one control appear to receive focus twice.
- Making static text focusable is not forbidden, but should not create confusing or tedious orders.

**Who benefits.** Keyboard users with mobility impairments, screen reader users, people with reading or cognitive disabilities who are disoriented by jumps, screen magnifier users who see only a small part of the page and may interpret a field in the wrong context.

**Common failures.** A form where Tab jumps between unrelated sections (name → checkbox → street → checkbox); positive `tabindex` values; modal dialogs that do not receive focus or leave focus on the page behind; focus lost to the top of the page after an action; off-screen or hidden content still receiving focus.

**Related.** 1.3.2, 2.1.1, 2.4.7, 2.4.11, 3.2.1

=== 2.4.4
**Intent.** Help users understand what each link does so they can decide whether to follow it — without complicated strategies. Screen reader users often browse a list of links or Tab from link to link, so the purpose must be clear from the link itself or from context they can reach without moving away.

**Where the purpose can come from.**
- **The link text alone** — preferred whenever possible ("2026 annual report (PDF, 2 MB)").
- **The link text together with its programmatically determined context:**
    - the same sentence, paragraph or list item;
    - the same table cell, or its header cell in a data table;
    - the heading immediately preceding the link (as a supported technique);
    - an accessible name or description added with `aria-label`, `aria-labelledby` or `aria-describedby`, or visually hidden text inside the link.
- For a link to a document or application, its name is enough.
- Context works best **before** the link; if the vague text comes first and the explanation after, screen reader users reading in order get confused.

**Exception.** Links whose purpose would be ambiguous to everyone — e.g. "Door 1", "Door 2" in a game meant to create suspense. But any context available on the page must be used.

**Best practices.**
- Links with the same destination use the same text (required across pages by 3.2.4); different destinations use different text.
- An image inside a link with adjacent text: give the image empty alt so the purpose is not repeated.
- When offering formats, the title link can be followed by short "PDF" and "MP3" links in the same list item.
- Links to accessible alternate versions should say so.

**Who benefits.** Screen reader users, people with motor impairments (avoiding unnecessary navigation and back), people with cognitive limitations who are disoriented by following wrong links.

**Common failures.** Many "Click here", "Read more" or "More" links with no programmatic context; image links without alt text; icon-only links with no accessible name; link text that describes something different from the destination; context only available visually (e.g. a card image) and not programmatically.

**Related.** 2.4.9, 2.4.2, 2.5.3, 3.2.4, 1.1.1

=== 2.4.5
**Intent.** Let users locate a page in the way that suits them. Some people prefer search, others a site map or table of contents, others browsing through navigation.

**What is required.** More than one way to locate each page within a set of pages. Common combinations:
- Main navigation **plus** site search.
- Navigation plus a site map or A–Z index.
- Navigation plus a table of contents, related links, or links between pages.
- For a very small site (3–5 pages) where all pages are linked from the home page, links on every page to all others can be enough.

**Exception.** Pages that are a step in, or the result of, a process: steps of a checkout or wizard, a funds transfer confirmation, search results. These can be reached only by performing the process.

**For digital publications.** A table of contents, index and page-break navigation help readers of EPUB and similar formats find and share their position.

**Who benefits.** People with visual impairments who find search faster than navigating long menus with a magnifier or screen reader; people with cognitive disabilities who find a site map or search easier than a hierarchy; anyone with a different navigation preference.

**Common failures.** A large site with only one navigation path and no search or site map; pages not linked from anywhere except deep within another page; search that excludes parts of the site.

**Related.** 2.4.8, 3.2.3, 2.4.1

=== 2.4.6
**Intent.** Help users understand what information a page contains and how it is organised, through headings and labels that describe the topic or purpose. Clear headings make it possible to predict what a section contains; clear labels identify components.

**What makes a heading or label descriptive.**
- Accurate and specific to the content or control: "Delivery address", not "Section 2"; "Search" for a search field.
- Need not be long — a word or even a single character may suffice if it is a clear cue in context.
- Images can act as labels if their meaning is widely understood in context (a magnifier icon named "Search" next to a text field). The same icon can mean something else elsewhere (zoom next to an image).
- Consistent section headings across similar pages (e.g. "Summary", "Introduction", "Conclusion" in every conference paper) help orientation.

**What this criterion does not require — and where that is covered.**
- It does **not** require headings or labels to exist — required labels for inputs are 3.3.2.
- It does **not** require correct markup — that is 1.3.1. Content can pass one and fail the other: a descriptive heading styled as bold text passes 2.4.6 but fails 1.3.1; a correctly marked-up but vague `<h2>Info</h2>` passes 1.3.1 but fails 2.4.6.
- It does **not** cover the accessible name — that is 4.1.2. A control can have an `aria-label` and pass 4.1.2 while failing 2.4.6 if the label is unclear.

**Who benefits.** People who read slowly or have limited short-term memory, screen reader users navigating by heading lists or tables of contents, everyone scanning a page.

**Common failures.** Generic headings ("More", "Information", "Section 1"); headings that do not match the content below; duplicate labels for fields with different purposes ("Name" for both the user and the recipient); labels that do not explain the expected input ("Value").

**Related.** 1.3.1, 2.4.10, 3.3.2, 4.1.2, 2.5.3

=== 2.4.7
**Intent.** Help people know which element has keyboard focus. Without a visible focus indicator, sighted keyboard users cannot tell where they are or what a keystroke will act on.

**What is required.**
- Any keyboard-operable interface has **at least one mode of operation** in which the focus indicator is visible. Browsers may show focus rings only for keyboard use (as with `:focus-visible`); that is acceptable, because keyboard use is the mode in question.
- The indicator must **not be time-limited** — it stays visible while the element has focus.
- The criterion does not specify the form: an outline, border, background change, underline, caret in a text field, or highlighted text all count as long as they are visible.

**Relationship to other criteria.**
- **1.4.11 Non-text Contrast:** an author-styled focus indicator must have at least 3:1 contrast against adjacent colours (browser defaults are exempt).
- **2.4.13 Focus Appearance (AAA):** sets size and contrast requirements for the indicator.
- **2.4.11 Focus Not Obscured:** the focused element must not be hidden behind other content.
- **1.4.1:** a focus change shown only by a change of hue may fail Use of Color.

**Best practice.** Provide a clear indicator for mouse users too where helpful; use a thick outline with an offset that works on all backgrounds.

**Who benefits.** Keyboard users, switch and speech input users, people with attention, short-term memory or executive function limitations who need to see where they are.

**Common failures.** `outline: none` or `outline: 0` without a replacement; focus styles only defined for `:hover`; focus indicators with the same colour as the background; focus indicators that fade out after a moment; custom widgets that move focus to elements with no visible style.

**Related.** 1.4.11, 2.4.11, 2.4.13, 2.1.1, 2.4.3

=== 2.4.8
**Intent.** Give users a way to orient themselves within a set of web pages, a website or an application, and to find related information. Knowing where you are reduces confusion, especially for people with cognitive disabilities.

**Ways to provide location information.**
- **Breadcrumbs** showing the path from the home page to the current page ("Home › Products › Laptops").
- **Indicating the current item in navigation** — visually and programmatically with `aria-current="page"`.
- **A site map** that shows the structure, with the current page identifiable.
- **Step indicators** in multi-step processes ("Step 2 of 4: Delivery").
- **Page titles and headings** that identify the section and page (e.g. "Laptops – Products – Example Shop").
- Links to the main sections from every page.

**Who benefits.** People with cognitive disabilities and short-term memory limitations, screen reader and magnifier users who see only part of the page, anyone arriving from a search engine deep in a site.

**Common failures.** No indication of where the page sits in the site; a navigation menu that does not highlight the current section; multi-step forms without any step indicator.

**Related.** 2.4.2, 2.4.5, 3.2.3

=== 2.4.9
**Intent.** Make the purpose of every link clear from the link text alone, so links can be understood out of context — for example in a screen reader's list of links.

**Difference from 2.4.4.** At Level A, surrounding context (sentence, paragraph, list item, table cell or header) can explain a link. At AAA, the link text itself — including its accessible name — must identify the purpose. "Read more" after a news summary passes 2.4.4 but fails 2.4.9.

**The "mechanism" option.** The criterion requires that a mechanism *is available* to make link purpose clear from link text alone. Authors can either:
- write every link to be self-explanatory by default, or
- offer a way to switch between short links and full links — some users find long repetitive links slower, others need full ones. Example: a list of 100 books with short "PDF", "MP3" links, and a setting that expands them to "Gulliver's Travels, PDF".
Visually hidden text or an accessible name that includes the full purpose (e.g. visible "MP3", accessible name "Gulliver's Travels, MP3") also meets it.

**Exception.** Links whose purpose is ambiguous to everyone (e.g. a game's "Door 1"). But any context available on the page must be put into the link text.

**Best practices.** Same destination, same text; different destinations, different text (see 3.2.4). Link text and destination page title should match.

**Who benefits.** Screen reader users scanning link lists, people with motor impairments who want to avoid visiting pages they do not need, people with cognitive limitations who get disoriented following the wrong links.

**Common failures.** Multiple "Read more", "Details" or "Download" links leading to different places; links named only by format ("PDF") without the document title; image links with generic alt text ("link", "arrow").

**Related.** 2.4.4, 2.4.2, 3.2.4

=== 2.4.10
**Intent.** Where content is organised into sections, provide headings that introduce them. Headings reveal the organisation of the content, make navigation within it easier, and give readers mental "handles" that aid comprehension.

**What it requires.**
- Sections of writing — chapters, topics, groups of settings, parts of a menu — have headings.
- "Heading" is meant broadly, including titles.
- Visual separation (horizontal rules, boxes, spacing) is not enough on its own to identify sections; it can complement headings.
- Correct heading markup is covered by 1.3.1; descriptive headings by 2.4.6. This criterion adds the requirement that sections actually *have* headings.

**Scope.**
- Covers sections within content, not user interface components (those are 4.1.2).
- At AAA because it cannot apply to all content: a pre-existing document posted as is, or a long letter where headings would be strange.

**Examples.** A restaurant menu with headings for Starters, Soups, Mains, Desserts; a settings page with headings for each group of related settings; a long guide with chapter and sub-chapter headings.

**Who benefits.** Blind users, who learn when they enter a new section and what it is about; people with learning disabilities who use headings to understand the overall structure; keyboard and screen reader users who jump from heading to heading; anyone looking for updated content in a part of the page.

**Common failures.** Long articles or documents with no headings; sections separated only by lines, boxes or bold paragraphs; application pages with groups of settings that have no group headings.

**Related.** 1.3.1, 2.4.6, 2.4.1

=== 2.4.11
**Intent.** Ensure that a component receiving keyboard focus is at least **partially visible** — not entirely hidden by author-created content. Sighted keyboard, switch and voice users need to see where focus is; when they cannot, they do not know how to proceed or think the page has stopped working.

**What typically hides focus.** Sticky headers and footers, cookie banners, fixed chat widgets, non-modal dialogs, and toolbars that stay on screen while the user tabs through content underneath.

**What passes at AA.**
- The focused component may be **partly** obscured — but the more is hidden, the harder it is to see; aim for no overlap (that is 2.4.12, AAA).
- The criterion checks the **component**, not its focus indicator (unless the indicator is inside the component). If the indicator is fully hidden, 2.4.7 may fail.
- Semi-transparent or blurring overlays do not "entirely hide" the component, but may fail 1.4.11 if the focus indicator loses contrast.

**Ways to pass.**
- `scroll-padding-top` / `scroll-padding-bottom` equal to the height of sticky bars, so focused items scroll into a clear area.
- Make banners **modal** (must be dismissed before using the page) or have notifications close when they lose focus.
- Make sticky elements static at small viewport sizes and high zoom.

**User-opened and user-movable content.**
- **Non-persistent disclosures** (menus, selects, comboboxes, date pickers, tooltips) close when focus leaves, so they do not obscure focus — unless they are allowed to persist.
- **Persistent disclosures** (accordions, side navigation, chat windows) pass if they push or reflow content rather than overlap it, open into empty space, keep focus inside until closed, or can be hidden with Esc.
- Content the user opened may cover the focused item if the user can reveal it **without moving focus** — e.g. Esc closes a chat popover, arrow keys scroll the page, F6 switches overlays.
- For panels the user can move, only their **initial position** is assessed.
- **Modal dialogs** built correctly always pass: they take focus, so the focused item is in the dialog.

**Who benefits.** Sighted keyboard users and users of switches, voice input and on-screen keyboards; low-vision users using magnification; people with attention or memory limitations who need to find the focus.

**Common failures.** Tabbing through links that disappear completely under a fixed cookie banner or sticky footer; a non-modal dialog that does not take focus and does not close on blur, hiding content behind it; fixed ads covering focused controls at high zoom.

**Related.** 2.4.7, 2.4.12, 2.4.13, 1.4.10, 1.4.13

=== 2.4.12
**Intent.** Ensure that a component receiving keyboard focus is **fully visible** — no part of it hidden by author-created content.

**What changes compared with 2.4.11.**
- Any overlap fails, not just complete obscuring. A sticky footer covering the bottom half of a focused button fails.
- Semi-transparent, blurring or dimming overlays on top of the focused component also fail — even if it remains recognisable — because they make it harder to tell what has focus. They may additionally fail 1.4.11 and 2.4.13.
- As in 2.4.11, the component is evaluated, not its external focus indicator (unless the indicator is part of the component).

**Ways to pass.** The same techniques as 2.4.11, applied strictly: scroll padding equal to the full height of sticky elements; modal banners that must be dismissed; notifications that take focus and disappear when they lose it; layouts that push content rather than overlay it.

**Examples.** A sticky footer with scroll padding so that every focused item appears entirely above it; a large modal cookie dialog that keeps focus inside until dismissed.

**Who benefits.** Sighted keyboard and switch users, voice input users, people using magnification, people with attention or memory limitations.

**Common failures.** Focused items partially hidden under sticky headers, footers, toolbars or chat buttons; dimmed overlays over focused content.

**Related.** 2.4.11, 2.4.7, 2.4.13

=== 2.4.13
**Intent.** Ensure the keyboard focus indicator is clearly visible and discernible — not just present (2.4.7), but large enough and with enough contrast. Small or subtle changes are missed by many people, including older users and people with low vision.

**The two requirements — an area of the indicator must meet both.**
- **Minimum area:** at least as large as a **2 CSS px thick perimeter** of the unfocused component (or its bounding box). It does not have to be an outline — only at least that large. For a rectangle w × h, roughly 4w + 4h px²; e.g. 480 px² for a 90 × 30 px button.
- **Change of contrast:** at least **3:1 between the same pixels** in the focused and unfocused states. This differs from 1.4.11, which measures contrast between adjacent colours in one state.

**Practical guidance.**
- The simplest pass: a solid outline at least 2 px thick around the component, ideally with `outline-offset`, in a colour with at least 3:1 against the background.
- Indicators **inset** inside the component must be thicker than 2 px (e.g. 3 px) to reach the area.
- For non-rectangular components, the outline may follow the shape or its bounding box.
- Only the part of the indicator meeting 3:1 counts toward the area (relevant for gradients and two-tone indicators).
- Changing the whole component's colour can pass if the new colour has 3:1 against the old one, but it is hard to notice when components cannot be compared side by side — not best practice.
- Prefer indicators that scale with the component, so they still meet the area in responsive variations.
- On varied backgrounds (images, parallax), use a two-colour indicator (e.g. dark and light rings) to guarantee contrast everywhere.
- Inline links wrapping over lines: `outline` or `border` both qualify.

**Composite components.** In a tablist or menu, the focus indicator itself shows what is considered the component: an indicator around the whole group, around the sub-component, or both. Where a sub-component indicator is needed (focus can differ from selection), assess that one.

**Exceptions.** The indicator is determined by the user agent and cannot be adjusted by the author, or the indicator and its background are not modified by the author (browser defaults).

**Relationship to 1.4.11.** An indicator can pass one and fail the other: a light grey border may change enough from white (2.4.13) but not contrast with adjacent colours (1.4.11), and vice versa.

**Who benefits.** Sighted keyboard and switch users, people with low vision, older users, people with attention limitations.

**Common failures.** 1 px or dotted outlines; subtle background tint changes on focus (e.g. black to #555); focus shown only by a thin underline or small colour change; inset indicators only 2 px thick; indicators that disappear against some backgrounds.

**Related.** 2.4.7, 1.4.11, 2.4.11, 2.4.12

=== 2.5.1
**Intent.** Ensure content can be operated with a range of pointing devices and abilities. People who cannot perform precise gestures, or who use a head pointer, eye-gaze system, speech-controlled mouse or a single finger or stick, may be unable to do multipoint or path-based gestures.

**Two kinds of gesture covered.**
- **Path-based:** the movement along a path matters — swiping or flicking (recognised only in a mostly straight line at some speed), tracing a shape, moving strictly along a track. The exact start and end points may not even matter.
- **Multipoint:** two-finger pinch or spread, a split tap (one finger resting, another tapping), two- or three-finger taps or swipes.

**What is required.** Every function using such gestures can also be done with a **single pointer without a path**: tap, click, double tap or click, long press, click-and-hold. The alternative must not rely on dragging either (that would fail 2.5.7).

**Path-based gesture vs. dragging.**
- In dragging, only the start and end points matter — the user grabs an object and drops it anywhere along any route. That is covered by 2.5.7, not 2.5.1.
- Typical sliders and draggable carousels use pointer capture and let the pointer drift, so they are dragging. If a slider loses the thumb when the pointer strays from the track, it is both, and may fail both criteria.

**Keyboard is not enough.** Keyboard operability (2.1.1) does not satisfy this criterion: some users rely entirely on pointers, and clicking a labelled control is far easier for them than emulating keystrokes.

**Out of scope.** Gestures defined by the operating system, browser or assistive technology — system swipes, browser back-swipe, native scroll flinging, screen reader gestures.

**Essential exception.** Functions inherently path-based, such as drawing a signature (although confirming identity need not be).

**Who benefits.** People with motor impairments, users of alternative pointing devices, one-handed or one-finger users, and people with cognitive disabilities who do not understand custom gestures.

**Common failures.** Maps zoomable only by pinch; carousels or galleries navigable only by swipe; swipe-to-delete or swipe-to-reveal actions with no button; two-finger gestures to rotate or zoom with no controls.

**Related.** 2.5.2, 2.5.7, 2.1.1, 2.5.4

=== 2.5.2
**Intent.** Make it easier to prevent accidental or erroneous pointer input. People with motor, visual or cognitive disabilities often touch or click the wrong target; they need a chance to back out before an action happens.

**At least one must be true for single-pointer functions.**
- **No down-event:** nothing executes on press (mousedown, touchstart, pointerdown).
- **Abort or undo:** the function completes on release (up-event), and the user can abort before completing or undo afterwards.
- **Up reversal:** release reverses whatever press did (press-and-hold to preview, release to dismiss).
- **Essential:** completing on press is essential.

**Why up-event activation helps.** When activation happens on release, users can see what they pressed and, if wrong, slide the pointer or finger off the target before lifting — the action is cancelled. JavaScript's `click` event already fires on release and works for mouse, touch and keyboard, so using it normally passes.

**Complex interactions.** For drag and drop (press, move, release), provide a way to abort — dropping back in the original place or outside a valid target reverts the move — or offer undo or confirmation.

**Essential down-event activation.** Keyboard and keypad emulation (keys act on press, like physical keys — and Backspace provides an undo); an on-screen piano; a game where precise press timing is the point (e.g. a shooting game).

**Scope.** Applies to content that interprets pointer actions, not to controls of the browser or assistive technology.

**Who benefits.** People with tremor and other motor impairments, people with low vision who misjudge targets, people with cognitive limitations, and everyone who taps the wrong thing.

**Common failures.** Actions (delete, submit, navigate, purchase) triggered on `mousedown`, `touchstart` or `pointerdown`; drag-and-drop with no way to cancel a drop; menus that activate an item on press.

**Related.** 2.5.1, 2.5.7, 3.3.4

=== 2.5.3
**Intent.** Make the words that visibly label a component also part of its programmatic (accessible) name, so people can rely on what they see. Speech-input users say the visible label to operate controls; screen reader users who can see the screen expect to hear what they see.

**What is required.** For components with a visible text label (or image of text), the accessible name **contains** that text. Best practice: the name **starts with** the visible text ("Search" → "Search the catalogue").

**Why mismatches matter.**
- A speech user saying "click Send" fails if the button's name is "Submit form".
- A name different from the label acts as a hidden voice command that can be triggered accidentally.
- Mismatches add cognitive load for users who must remember different words.
- A component with a visible label but no accessible name at all fails both 4.1.2 and this criterion.

**What counts as the visible label.** Conservatively, only the adjacent text: to the left of (or above) inputs and selects, to the right of checkboxes and radios, inside buttons, links and tabs, or below an icon. Headings, instructions and group legends are not labels — their context can go in `aria-describedby`. Placeholder text can count only when there is no other visible label.

**Details.**
- Case and punctuation are ignored: "First Name:" and "first name" match; "Next…" and "Next" match.
- Symbolic characters are not labels: a "B" bold button should be named "Bold", a ">" should be named "Next".
- Mathematical expressions are labels: keep the formula as shown ("11×3=33").
- Text in parentheses may be left out of the name ("Name (required)" → "Name"), but the information must be conveyed another way (e.g. `required`).
- `aria-label` and `aria-labelledby` override visible labels in the name calculation — the usual cause of mismatches. Use them carefully when a visible label exists.

**Who benefits.** Speech recognition users, screen reader users who see the screen, people with cognitive disabilities.

**Common failures.** Visible "Buy now" with `aria-label="Add product to basket"`; a link "Read more" named "Article details"; an input labelled "Email" with `aria-label="Your contact address"`; icon-plus-text buttons whose name omits the text.

**Related.** 4.1.2, 2.4.6, 1.1.1, 3.3.2

=== 2.5.4
**Intent.** Ensure that functions triggered by moving a device (shaking, tilting) or by gesturing towards it (wave to a camera) can also be operated with conventional controls, and that motion response can be turned off. Some people have devices on a fixed mount or cannot make the movements; others trigger sensors accidentally because of tremor.

**What is required — both:**
- The function can also be operated through **user interface components** (a button, a link, a control).
- Responding to motion can be **disabled** to prevent accidental actuation — via an application setting or by respecting an operating system setting.

**Scope.**
- Covered: content that interprets device motion (accelerometer, gyroscope) or user gestures picked up by sensors or cameras as input — shake to undo, tilt to scroll, move to pan a 360° photo, hand gestures, face or eye gestures to a camera.
- Not covered: a user's movement through space (geolocation, beacons); pointing a camera at a QR code or document; incidental movement needed to type, click, touch or operate assistive technology.

**Exceptions.**
- **Supported interface:** motion used through an accessibility-supported interface (e.g. head-tracking assistive technology).
- **Essential:** motion is essential and alternatives would invalidate the activity — a pedometer, a fitness app counting movements, a level tool.

**Examples.** Shake to undo with an Undo button next to the field and a setting to turn shaking off; tilt to turn pages with Previous/Next buttons; moving the phone to explore a panorama with on-screen arrow controls.

**Who benefits.** People with devices mounted on wheelchairs, people with motor impairments who cannot hold or move a device steadily, people with tremor, and anyone who cannot move their device at the moment.

**Common failures.** Undo available only by shaking; games or viewers controllable only by tilting; motion features that cannot be turned off.

**Related.** 2.5.1, 2.1.1, 1.3.4

=== 2.5.5
**Intent.** Help people who have trouble activating small targets — because of hand tremor, limited dexterity, or the coarse precision of touch — by making targets at least 44 × 44 CSS pixels.

**What is measured.** The target area that responds to the pointer, not just the visible icon. Padding can enlarge a small icon's target.

**Exceptions.**
- **Equivalent:** another control on the same page performing the same function is at least 44 × 44.
- **Inline:** targets within a sentence or block of text, including footnote links and help icons at the end of a sentence. (A link that is a full sentence on its own, not in a block of text, must meet the size.)
- **User agent control:** size determined by the browser and not modified by the author.
- **Essential:** a particular presentation is essential to the information.

**When to go larger than the minimum.** Frequently used controls; actions that cannot be easily undone; controls near screen edges or hard to reach; controls in sequential tasks.

**Relationship to 2.5.8.** 2.5.8 (AA) requires 24 × 24 or sufficient spacing; 2.5.5 (AAA) requires 44 × 44 without a spacing alternative.

**Who benefits.** Touchscreen users, people with tremor or limited fine motor control, one-handed users, people using devices on the move (e.g. on public transport), people using knuckles or part of a finger, people with low vision who see larger targets better.

**Common failures.** Small icon buttons (close, share, edit) with tiny hit areas; dense toolbars; small checkboxes and radios with no clickable label; pagination links smaller than 44 px.

**Related.** 2.5.8, 2.5.1

=== 2.5.6
**Intent.** Let people use and switch between different input mechanisms — touch, mouse, keyboard, stylus, speech — whenever they want.

**What is required.** Content does not restrict use of input modalities available on the platform. A phone's primary input is touch, but a user may pair a mouse or keyboard; a laptop user may switch between trackpad, touch and keyboard; a speech user may switch to a mouse mid-task.

**What breaks it.**
- Detecting a touchscreen and then disabling mouse or keyboard handlers.
- Assuming the first input detected is the only one ("keyboard user" or "touch user" modes that lock out others).
- Listening only to touch events or only to mouse events instead of pointer events.

**Exceptions.**
- **Essential:** e.g. a touch-typing tutor that must use the keyboard.
- **Security:** a restriction required for security.
- **User settings:** respecting a user's own choice to restrict input.

**Examples.** A user opens a menu with the mouse, then navigates items with arrow keys; a user with a mobility impairment pairs a keyboard and mouse to a phone and the content still works; a secondary touch monitor attached mid-session works immediately.

**Who benefits.** People who combine inputs depending on task, fatigue or circumstances; people with mobility impairments who use alternative devices on mobile platforms.

**Common failures.** Mobile sites that ignore physical keyboards; web apps that disable mouse hover or click handling when touch is present; interfaces that require touch gestures even when a mouse is connected.

**Related.** 2.1.1, 2.5.1, 2.5.7

=== 2.5.7
**Intent.** Ensure that functionality operated by dragging can also be done with a single pointer **without dragging**. Dragging needs four actions — press, hold, move while holding, release — and many people cannot hold a contact while repositioning; trackballs, head pointers and eye-gaze systems make dragging cumbersome and error-prone.

**What counts as an alternative.**
- Clicking or tapping a slider track to move the thumb there.
- Arrow or +/− buttons to move a map, a carousel, or a list item.
- "Move to…" menus or buttons to move cards between kanban columns.
- Click one item, then click the destination (drawing connecting lines, selecting a rectangle corner by corner).
- A text input to type a value (a number next to a slider, hex values next to a colour wheel) — text entry counts as single-pointer via the on-screen keyboard.
- The alternative can be a different component on the same page, as long as the function is equivalent.
- It must not be a path-based gesture such as swipe (2.5.1).

**Separate from keyboard access.** 2.1.1 requires keyboard operation of drag features; this criterion requires pointer operation without dragging. Touchscreen users may have no keyboard, so a keyboard alternative alone does not pass — the two are evaluated independently.

**Out of scope.**
- Scrolling and dragging provided by the browser: scrollbars, touch scrolling of the page, pull-to-refresh, `overflow` scroll areas.
- But if content suppresses native scrolling and implements its own drag-to-scroll, it is in scope.

**Exceptions.** Dragging is essential (e.g. freehand drawing — though even then alternatives help), or the function is determined by the user agent and not modified.

**Who benefits.** People with motor impairments, tremor or limited strength; users of trackballs, head pointers, eye-gaze, speech-controlled mouse emulation.

**Common failures.** Sortable lists, kanban boards or file uploads that only support drag and drop; sliders and range selectors operable only by dragging the thumb; carousels that only move by dragging; image croppers with drag-only handles.

**Related.** 2.5.1, 2.1.1, 2.5.2

=== 2.5.8
**Intent.** Help ensure targets can be activated without accidentally activating an adjacent one. People with tremor, spasticity, quadriplegia or limited fine motor control, and users of less precise input devices, often hit the wrong control when small targets are close together. It also makes touch interfaces easier for everyone.

**The size requirement.** Each target is at least **24 × 24 CSS px**: it must be possible to fit a solid 24 × 24 px square, aligned to the page axes, entirely within the target.

**The spacing alternative.** An undersized target passes if a **24 px diameter circle** centred on its bounding box does not intersect another target or another undersized target's circle. Small targets with enough space around them pass; small targets packed together fail. Best practice is still to meet the size regardless of spacing, and to aim for 44 × 44 (2.5.5) for important controls.

**Exceptions.**
- **Equivalent:** another control on the same page performs the function and meets the criterion.
- **Inline:** targets in a sentence, or whose size is constrained by the line height of surrounding text (links in paragraphs, lists of inline links). Reflow makes their positions unpredictable, and readable line height matters more.
- **User agent control:** size determined by the browser and not modified (e.g. the date picker calendar of `<input type="date">`).
- **Essential:** the size and spacing are fundamental to the information (pins at true positions on a map, dense data visualisations) or legally required (forms that must replicate paper forms). Offer alternatives where practical.

**Spatial targets.** A slider, colour gradient picker, or editable text area where position selects a value counts as one target.

**Who benefits.** People with hand tremor, spasticity, limited dexterity; users of head pointers, eye-gaze and switch-operated pointers; touchscreen users; older users.

**Common failures.** Clusters of small icon buttons (edit, delete, share) under 24 px with less spacing; small close buttons next to other controls; pagination or star-rating controls packed tightly; custom checkboxes or radios with tiny hit areas and no clickable label.

**Related.** 2.5.5, 2.5.1, 2.5.2

=== 3.1.1
**Intent.** Provide the information user agents need to present text correctly by identifying the default human language of each page. Screen readers load the right pronunciation rules, browsers render characters and scripts properly, braille translators apply the right rules, and media players display captions correctly.

**How it is met.**
- In HTML: the `lang` attribute on the `<html>` element with a valid BCP 47 code — `lang="pl"`, `lang="en"`, `lang="en-GB"`, `lang="de"`.
- In other formats: the equivalent language property (e.g. document language in PDF or Office files).

**Which language is the default.**
- The language used most on the page.
- If several are used equally, the first one used.
- Example: a German page with some English passages is `lang="de"`; the English passages are then marked under 3.1.2.

**Multilingual sites.** Each page states its own language. W3C strongly encourages meeting 3.1.2 (marking passages in other languages) even when aiming only for Level A.

**Why it matters for speech.** Without the correct language, a Polish page read by an English voice is unintelligible; numbers, dates and abbreviations are also read by the wrong rules.

**Who benefits.** Screen reader and text-to-speech users, braille users, people with reading, cognitive or learning disabilities who use text-to-speech, people relying on captions, and users of translation tools.

**Common failures.** Missing `lang` attribute; an invalid or misspelled code (`lang="pl-PL "`, `lang="polish"`); a wrong language copied from a template (e.g. `lang="en"` on a Polish page); language set only in a `<meta>` tag rather than on `<html>`.

**Related.** 3.1.2, 1.3.1

=== 3.1.2
**Intent.** Let user agents correctly present passages and phrases written in a language other than the page's default — applying the right pronunciation, braille rules, character rendering and text direction.

**What needs marking.** Any passage or phrase — even a single word — in a different language, unless an exception applies. In HTML: `lang` on the element containing it (`<span lang="de">Treppenwitz der Weltgeschichte</span>`). Content without its own `lang` inherits the page language.

**Exceptions.**
- **Proper names:** brands, people, places ("Albert Camus" in an English text need not be marked French).
- **Technical terms:** Homo sapiens, hertz, habeas corpus, Alpha Centauri.
- **Words of indeterminate language.**
- **Words that have become part of the surrounding language:** "rendezvous" in English, "podcast" in French. In doubt, ask whether it would be pronounced the same (apart from accent) in the surrounding language. Single words are usually considered part of the surrounding language unless a change is clearly intended.
- Best practice (not required): mark borrowed words and names anyway when pronunciation suffers, especially if they use another writing system (`lang="zh-Latn-pinyin"`).

**Why it matters.**
- Speech synthesisers switch pronunciation; unmarked, French "voiture" is read as English "voyture".
- Braille translation handles accented characters and avoids wrong contractions.
- Correct text direction for right-to-left languages, and correct glyphs.
- Machine translation and dictionary lookups work better.

**Language switchers.** Links to other language versions ("Deutsch", "Français", "Polski") should each carry `lang` matching their text.

**Known limitation.** Accessible names are flat strings, so a language change inside a link or button name may not be announced (e.g. in a screen reader's links list). This is a user agent limitation and does not fail the criterion — evaluate the markup, not just the speech output.

**Who benefits.** Screen reader and text-to-speech users, braille users, people with reading and learning disabilities, caption users.

**Common failures.** Quotes, titles or passages in another language without `lang`; language switchers without `lang`; multilingual content (e.g. bilingual forms) where the second language is unmarked.

**Related.** 3.1.1, 1.3.1

=== 3.1.3
**Intent.** Some disabilities make it hard to understand figurative language, idioms, jargon and words used in specialised or unusual ways. Provide a mechanism to identify the specific definition intended.

**What counts as "unusual or restricted".**
- **Idioms and figurative language:** "it's raining cats and dogs", "spill the beans".
- **Jargon:** terms specific to a field, profession or community, used for a general audience.
- **Words used in a restricted sense:** WCAG's own "text", "content" or "mechanism"; a "cascade" of dictionaries.
- Authors may assume readers use context to disambiguate ordinary ambiguous words, and may consider the intended audience: medical terms on a site for doctors are not unusual for that audience.
- New, made-up or invented words are **not** exempt, since they may confuse everyone.

**Ways to provide definitions.**
- Define the word in the text the first time it is used.
- Link words to a glossary on the same page or site.
- Inline definitions with `<dfn>`, or a description list of terms.
- A search or lookup mechanism (e.g. a cascade of dictionaries, specialised first).

**Encouraged beyond AAA.** W3C encourages providing definitions for specialised information aimed at non-specialists even when targeting only A or AA.

**Who benefits.** People with cognitive, language and learning disabilities who have difficulty decoding or understanding words and phrases; screen magnifier users who lose the surrounding context; non-native readers.

**Common failures.** Public service or legal pages full of unexplained terms; idioms or metaphors used in instructions; product terminology used without explanation.

**Related.** 3.1.4, 3.1.5, 3.1.6

=== 3.1.4
**Intent.** Ensure users can access the expanded form or meaning of abbreviations — acronyms, initialisms and shortened words.

**Why abbreviations confuse.**
- Some cannot be pronounced by normal rules ("rm" for "room").
- The same abbreviation can mean different things ("Dr. Johnson lives on Boswell Dr." — Doctor and Drive).
- Some acronyms are also ordinary words with different meanings ("JAWS" — Job Access With Speech).
- Some sound like words but are spelled differently (SMIL sounds like "smile").

**What is exempt.** Abbreviations that have **become part of the language**: listed as a word in a common dictionary ("laser", "radar"), or well-known organisation and product names used as words ("IBM", "NASA"). Other abbreviations are not exempt even if common.

**Ways to provide the expansion.**
- Expand at first use: "World Wide Web Consortium (W3C)".
- A glossary or list of abbreviations, linked from where they appear.
- `<abbr title="…">` (note: `title` alone is not reliably exposed to keyboard and touch users, so combine with another method).
- A lookup service or cascade of dictionaries, including a site-specific abbreviation list.

**Who benefits.** People who have difficulty decoding words, people with limited memory, people who struggle to use context, screen magnifier users who lose context, and anyone unfamiliar with the field.

**Common failures.** Government, medical or technical documents with many unexplained acronyms; abbreviations defined only once far from where they are used.

**Related.** 3.1.3, 3.1.5

=== 3.1.5
**Intent.** Content should be written as clearly and simply as possible. When text requires reading ability above **lower secondary education** (more than about nine years of school) — after removing proper names and titles — provide supplemental content or a simpler version. Authors can still publish complex content, while people with reading disabilities get help.

**Why lower secondary.** Text beyond that level is a severe obstacle for people with reading disabilities such as dyslexia — decoding word by word consumes the mental effort needed for understanding — and is considered difficult even for many people without disabilities.

**Education levels (UNESCO ISCED).**
- Primary: years 1–6.
- Lower secondary: years 7–9.
- Upper secondary: years 10–12.
- Advanced: more than 12 years.

**Assessing reading level.**
- Readability formulas for the language, or evaluation by qualified teachers against local standards.
- Remove or ignore proper names and titles of works, which cannot be simplified.
- For multilingual pages, assess each language that makes up at least 5% of the content in full sentences, and judge by the worst result.

**Kinds of supplemental content.**
- A plain-language summary (e.g. for each research article).
- An easy-to-read version of the text.
- Illustrations, diagrams, graphic organisers.
- Spoken versions (audio, synthetic speech), or sign language.
- Content written directly at lower secondary level needs nothing extra.

**Why a testable measure.** "Easy to read" cannot be universal and could not be tested; reading level introduces testability while encouraging clear writing.

**Who benefits.** People with reading disabilities, people with cognitive or intellectual disabilities, people reading in a second language, deaf people whose first language is a sign language.

**Common failures.** Legal terms, policies, medical or financial information written at university level with no summary or simplified version.

**Related.** 3.1.3, 3.1.4, 3.3.5

=== 3.1.6
**Intent.** Help people understand content when the meaning of a word depends on how it is pronounced. Blind users hearing a word read incorrectly by a screen reader may find it even harder to understand than sighted readers.

**When it applies.** Only when meaning is ambiguous **in context** without knowing the pronunciation.
- **Heteronyms:** words spelled the same with different pronunciations and meanings — English "desert" (abandon) vs "desert" (arid region), "lead", "record". If the sentence makes it clear, nothing is required.
- **Characters with multiple readings:** Japanese kanji often have several pronunciations; personal names especially may be read wrongly by screen readers.
- **Shared characters pronounced differently by language:** Chinese and Korean quotations written in characters also used in Japanese.

**Ways to provide pronunciation.**
- Phonetic text next to the word, e.g. kana in parentheses after kanji (screen readers will read both — first possibly wrong, then the correct reading).
- The HTML `<ruby>` element to show readings above the characters.
- Links to sound files with the correct pronunciation.
- Pronunciation in a glossary, linked from the word.

**Who benefits.** Blind and low-vision users of speech output, people with reading disabilities who have difficulty decoding words or using context.

**Common failures.** Names in Japanese or Chinese without readings where they are ambiguous; heteronyms in instructions where context does not resolve the meaning.

**Related.** 3.1.3, 3.1.2

=== 3.2.1
**Intent.** Keep functionality predictable as people move through a page: when a component receives focus, it must not trigger a change of context. Users explore pages by moving focus; if that alone causes something major to happen, they become disoriented or cannot reach what they want.

**What counts as a change of context.** A major change that can disorient users if it happens without their awareness:
- submitting a form,
- opening a new window or tab,
- moving focus to another component,
- navigating to another page,
- significantly rearranging the content so its meaning changes.
Small changes — showing help text near a field, highlighting, expanding a hint — are changes of content, not context, and are allowed.

**How focus arrives.** By keyboard (Tab, arrow keys) or by clicking into a field. Hovering the mouse does not move focus unless a script makes it do so. Clicking a button both focuses and activates it — the activation may change context; that is covered by user request, not by this criterion.

**Examples.**
- Pass: a select menu with jump destinations navigates only when the user activates an option with Enter or Space, not when arrowing or tabbing out.
- Fail: a help dialog opens whenever a field receives focus and steals focus, so keyboard users can never tab past the field.

**Who benefits.** People with visual disabilities who may not notice the change, people with cognitive limitations, people with motor impairments who move focus slowly, keyboard and screen reader users.

**Common failures.** Fields that submit or validate-and-redirect on focus; links or controls that open pop-ups or new windows on focus; scripts that move focus elsewhere (e.g. `this.blur()` or forcing focus to another field) when an element receives focus; modal dialogs opening on focus or hover.

**Related.** 3.2.2, 3.2.5, 2.4.3, 1.4.13

=== 3.2.2
**Intent.** Make entering data or selecting options predictable: changing a control's setting must not automatically cause a change of context — unless users were told beforehand. Unexpected changes confuse people who do not easily perceive them or are easily distracted.

**What "changing a setting" means.** Changing something about a control that persists after interacting with it:
- checking a checkbox or radio button,
- typing into a text field,
- choosing an option in a select or listbox,
- toggling a state button (`aria-pressed`), or a button that becomes disabled after use.
Not changing a setting (activation instead): following a link, pressing a submit button, a button that opens a dialog or menu and moves focus there. Those are user requests and are not covered.

**What is a change of context here.** Submitting a form, navigating to another page, opening a new window, moving focus elsewhere, or substantially changing the page so its meaning changes. Revealing extra fields within the same form (e.g. choosing "Meeting" shows a participants field) keeps the overall context and is fine.

**When automatic changes are allowed.** If the user has been advised **before** using the component — e.g. instructions at the start of a form: "Focus moves to the next field automatically when each part of the phone number is complete."

**Who benefits.** Blind and low-vision users who may not notice a new window or page (the Back button then behaves unexpectedly), people with reading, intellectual or cognitive disabilities, people who have difficulty interpreting visual cues.

**Common failures.** A select menu that navigates to a new page as soon as an option is chosen (keyboard users trying to arrow through options are taken away at the first move); forms submitted when the last field is filled or a radio is chosen; checkboxes that open a new window; auto-advancing focus between fields without prior notice.

**Related.** 3.2.1, 3.2.5, 3.3.2

=== 3.2.3
**Intent.** Encourage consistent visual layout and source order of navigation repeated across pages, so users who need to find the same thing again can predict where it is.

**What is required.** Navigational mechanisms repeated on multiple pages in a set appear in the **same relative order** each time, unless the user changes it.
- "Same relative order" means items keep their order relative to each other; items may be added or removed between them.
- Sub-navigation can expand within the menu; secondary navigation blocks can appear on some pages.
- Users may change the order themselves through preferences or adaptive user agents.

**What counts as navigational mechanisms.** Main menus, sub-menus, skip links, search, breadcrumbs, footer link lists, "skip to navigation" links, and other repeated navigation components.

**Why it matters.**
- Screen magnifier users see a small part of the screen and rely on spatial memory and page boundaries.
- Sighted users rely on visual cues and spatial memory.
- Blind users navigating sequentially rely on navigation appearing at a consistent point in the source order.

**Examples.** A search field that is the last item on every page; a skip link that is always the first link; a menu of seven sections that inserts sub-items when one is selected, without reordering the others.

**Who benefits.** People with cognitive and intellectual disabilities, people with low vision, blind users.

**Common failures.** Menu items appearing in a different order in different sections of the site; navigation moved from header to sidebar on some pages; skip links present on some pages and absent or elsewhere on others; personalised menus that reorder items without the user choosing to.

**Related.** 3.2.4, 3.2.6, 2.4.1, 2.4.5

=== 3.2.4
**Intent.** Identify components that have the same function consistently across a set of pages. Screen reader users in particular rely on familiarity with functions they have met before; different labels for the same function make a site much harder to use and add cognitive load.

**What "consistently" means.**
- The same function has the same label, accessible name and text alternative wherever it appears: "Search" everywhere, not "Search" on one page and "Find" on another.
- Consistent does not have to mean identical. "Page 2", "Page 3" for next-page links are consistent; "Print receipt" and "Print invoice" for printing different documents are consistent patterns.
- Different functions may have different names even with the same icon (a check-mark toggle named "approved" on one page and "included" on another).
- Applies to text alternatives of icons and images too.
- If two components on one page share a function with a component on another page, all three must be consistent.

**Scope.** Consistency across pages within a set. Consistency within a single page is best practice, not required by this criterion.

**Interaction with other criteria.** Same visible text but different `aria-label` values announces the buttons differently to assistive technology — a failure here and likely of 2.5.3. Two adjacent links (icon and text) to the same place should ideally be combined; at minimum their names must be consistent.

**Who benefits.** Screen reader users, people with cognitive limitations, people with reading difficulties who recognise functions by consistent icons, and anyone searching for a function by name.

**Common failures.** "Search" vs "Find" buttons doing the same thing; a download icon named "Download" on one page and "Get file" on another; the same icon button with different `aria-label` on different pages; inconsistent names for a shopping cart ("Basket", "Cart", "Bag").

**Related.** 3.2.3, 2.4.4, 2.4.9, 2.5.3

=== 3.2.5
**Intent.** Give users full control over changes of context: changes happen only when the user requests them, or there is a way to turn automatic changes off. Unexpected changes such as new windows or automatic form submission confuse people with motor impairments, low vision, blindness and cognitive limitations.

**What is required — one of:**
- Changes of context are **initiated only by user request** (activating a link, pressing a button).
- A **mechanism is available to turn off** automatic changes (a preference setting).

**Typical automatic changes to avoid.**
- Opening new windows or tabs without the user asking — a link click requests the content change, but opening a new window is a separate change and is not user-requested unless the user explicitly chooses it (or is clearly told).
- Pop-up windows on page load.
- Timed redirects and client-side refreshes — use server-side redirects (users never notice them) or an "Update now" button.
- Forms that submit automatically after selection.

**Nuances.**
- Some users benefit from automatic changes (e.g. single-switch users relying on system-driven scanning); content that changes context automatically only when user preferences allow it conforms.
- Some content, such as slide shows, inherently changes context; offering control over it is the goal.

**Who benefits.** Blind and low-vision users who may not notice a new window (and find Back no longer works), people with reading, intellectual and cognitive disabilities, people with motor impairments.

**Common failures.** `target="_blank"` links without warning; pop-ups on load; `<meta http-equiv="refresh">` redirects or reloads; content that auto-refreshes and resets the page.

**Related.** 3.2.1, 3.2.2, 2.2.1, 2.2.4

=== 3.2.6
**Intent.** Make help easy to find by placing it in the same place across a set of pages, when it is offered. People with some disabilities may be unable to complete a task without help — and if they cannot find it, they abandon the task, make mistakes, or ask people who may not keep their information safe.

**Which help mechanisms are covered.** If any of these appear on multiple pages, they must be in the same order relative to other content:
- **Human contact details:** phone number, email address, opening hours.
- **Human contact mechanism:** messaging, chat, contact form, social media channel.
- **Self-help option:** FAQ, "How do I…" page, support page.
- **Fully automated contact mechanism:** chatbot.
They may be on the page directly or via a direct link (e.g. "Contact" in the header).

**How consistency is assessed.**
- By **relative order** in the serialized page: content that comes before the help item on other pages comes before it here, and content after stays after.
- A visually different position with the same serial order does not fail (though it is less helpful).
- Compared within the same page variation — the same zoom level, orientation or breakpoint. Layout changes triggered by the user (zoom, viewport size) are allowed. Moving between pages or logging in does not count as a user-initiated change, unless logging in leads to a different set of pages.

**What it does not require.**
- Providing help at all — only consistency where help exists. Pages without the mechanism do not fail.
- Human help available at all times (though stating availability helps).
- Help inside PDFs or other downloadable documents.
- Consistency between different sets of pages (e.g. a product's marketing site and its application) — though it is best practice.
- Contextual help (field hints, spellcheck, instructions) — that is 3.3.2 and 3.3.5.

**Advice for cognitive accessibility (not required).** Offer contact for the team that can actually help; let people describe problems in their own words; say when no human support is available; chatbots should tolerate misspellings, offer human contact after about three failed attempts, and be dismissible and recallable easily.

**Who benefits.** People with cognitive and learning disabilities, people experiencing cognitive fatigue, and anyone who gets stuck on a task.

**Common failures.** "Contact us" in the header on some pages and only in the footer on others; a chat button that appears in different places in different sections; a help link placed before the navigation on some pages and after the main content on others.

**Related.** 3.2.3, 3.3.5, 3.3.2

=== 3.3.1
**Intent.** Make users aware that an input error occurred and let them determine what is wrong. Re-displaying a form without saying why the submission failed is not enough; the error must be identified and described **in text**.

**What counts as an input error.**
- Required information omitted.
- Information outside the required format or allowed values: an invalid postal code, a birth date in the future, letters in a numeric phone field, an invalid region code, a bid below the minimum.
- If the page silently corrects a value (e.g. clamps an out-of-range number), the user must still be told what changed.

**What the message must do.**
- **Identify the item in error** — which field.
- **Describe the error** in text — what is wrong.
- Telling the user how to fix it is 3.3.3; one message often satisfies both: "Email is not valid" passes 3.3.1; "Enter an email address in the format name@example.com" passes both.
- Colour, icons and highlighting are welcome **in addition to** text, never instead of it (see 1.4.1).

**Where to show errors.** Not prescribed: an error summary before the form, inline messages next to fields, an alert or dialog — any works if the errors are in text. Good practice: associate inline messages with fields (`aria-describedby`), mark fields `aria-invalid="true"`, and move focus to a summary or announce errors (4.1.3).

**Native HTML validation.** Browser validation (`required`, `type="email"`, `pattern`) meets this criterion in most browser/screen reader combinations, but has drawbacks: messages may disappear, do not scale with zoom, are generic (often insufficient for 3.3.3), and show only one error at a time. Check whether it is accessibility supported for your audience.

**Who benefits.** Blind and low-vision users and people with colour vision deficiency, who may miss visual-only error cues; people with cognitive, language and learning disabilities who need to understand why a submission failed.

**Common failures.** Errors shown only by a red border or icon; a generic "There are errors in the form" without saying which fields; the form simply reloading; error messages not associated with or near their fields; errors in an image without a text alternative.

**Related.** 3.3.3, 3.3.2, 4.1.3, 1.4.1, 4.1.2

=== 3.3.2
**Intent.** Provide labels or instructions so users know what input is expected — for every field, and for every option in radio buttons, checkboxes and similar choices — without cluttering the page.

**What needs labels or instructions.**
- Every form control that accepts input — not only *required* fields ("requires" means accepts or expects).
- Each option in a group (each radio button and checkbox), plus the group's question.
- Multi-part fields: "Given name" and "Family name" rather than one "Name" label for two fields; a phone number split into three fields needs labels for each part (e.g. a fieldset legend plus invisible labels).
- Not links or controls unrelated to data entry (expand/collapse buttons).

**What instructions should cover — where relevant.**
- Required fields and how they are marked.
- Expected formats, especially uncommon ones: "Date (DD-MM-YYYY)".
- Rules for valid input: password requirements, allowed characters in usernames.
- Help with values: e.g. a link to a list of valid codes.
- Long instructions can be shown when the field gets focus, but too much information is as harmful as too little.

**Visual labels.** Labels must be presented to all users, not just to assistive technology. A label conveyed only through `aria-label` passes 4.1.2 but fails 3.3.2. Image labels (e.g. a magnifier icon for search) are acceptable if widely understood; adding text helps.

**What is covered elsewhere.**
- Correct programmatic association (`<label for>`, fieldset/legend) — 1.3.1.
- Accessible name — 4.1.2.
- Whether labels are clear and descriptive — 2.4.6.

**Who benefits.** Everyone, especially people with cognitive, language and learning disabilities; labels and format examples prevent errors and the effort of fixing them.

**Common failures.** Placeholder text as the only label (disappears on typing, often low contrast); fields with no visible label; radio buttons with labels but no group question; unexplained format requirements that cause validation errors; required fields indicated only by colour.

**Related.** 1.3.1, 2.4.6, 3.3.1, 3.3.5, 4.1.2, 2.5.3

=== 3.3.3
**Intent.** When an input error is detected and suggestions for correcting it are known, provide them — unless doing so would compromise security or the purpose of the content. Knowing *that* something is wrong (3.3.1) is not enough for many people; without knowing how to fix it, they may abandon the form.

**What a good suggestion looks like.**
- States what is expected: "Enter the date as DD-MM-YYYY".
- Lists acceptable values: "Choose one of: January, February, … December" when "12" is typed for a month name.
- Offers an interpretation: "Did you mean 'December'?"; "Did you mean gmail.com?".
- Explains constraints: "Password must be at least 12 characters and include a number".
- Provides more help next to the field that caused the error.
- Suggestions can come from the author or from the user agent based on programmatic information.

**The exceptions.**
- **Security:** do not reveal which part of a login was wrong if that helps attackers ("username or password is incorrect" is acceptable).
- **Purpose:** do not give away answers in a test or quiz.

**Who benefits.** People with learning and cognitive disabilities, blind and low-vision users who cannot see context or examples on screen, people with motor impairments who want to minimise re-entry.

**Common failures.** "Invalid input" or "Error" with no explanation; messages that repeat the field name only ("Phone is invalid") when the expected format is known; browser-default messages that are too generic for the specific rule.

**Related.** 3.3.1, 3.3.4, 3.3.2

=== 3.3.4
**Intent.** Help people avoid serious, hard-to-reverse consequences of mistakes. People with reading disabilities may transpose digits, and people with motor disabilities may hit keys by accident; an error in a ticket date or share quantity can be costly and permanent.

**Which pages it applies to.**
- **Legal commitments:** contracts, agreements, applications with legal effect.
- **Financial transactions:** purchases, bookings, payments, stock trades.
- **Modifying or deleting user-controllable data:** data the user can view and change, such as a profile, address, records or invoices. The aim is to prevent mass or significant loss (deleting a file or record), not to confirm every save or edit.
- **Submitting test responses.**

**At least one safeguard.**
- **Reversible:** the submission can be undone (e.g. cancellation within a period).
- **Checked:** input is checked for errors and the user can correct them before submitting.
- **Confirmed:** a review step to check, confirm and correct information before finalising.

**Examples.** An order summary showing items, quantities, address and payment method with "Confirm" and "Edit" options; a trading site warning that an order will be after hours, explaining the risk, and allowing the user to cancel or confirm; "Are you sure you want to delete this record?" with an undo option.

**Who benefits.** Users with all kinds of disabilities who may be more likely to make mistakes or not notice them — people with reading, cognitive and motor disabilities in particular.

**Common failures.** One-click purchases with no review or cancellation; bank transfers submitted immediately; delete actions with no confirmation or undo; exam answers submitted without a review step.

**Related.** 3.3.6, 3.3.1, 3.3.3, 2.5.2

=== 3.3.5
**Intent.** Help users avoid mistakes by providing context-sensitive help — explanations available at the point where they are needed, so users can find out how to do something without losing track of what they are doing.

**When it is needed.** Only where labels alone do not explain the functionality — e.g. form questions that are hard to understand, unfamiliar terms, complex calculations or choices. Simple, self-explanatory fields need nothing more.

**Forms context-sensitive help can take.**
- A help link or button next to a field or question ("What is a CVV?").
- Instructions or examples beside the input.
- Expandable explanations or tooltips that meet 1.4.13.
- Step-by-step guidance or wizards for complex tasks.
- Spell-checking or suggestions for text input; help provided by the user agent based on programmatic information also counts.

**Making help usable.** Its existence should be obvious, and users should be able to get it whenever they need it, without leaving the task or losing their data.

**Who benefits.** People with writing disabilities, reading and intellectual disabilities, older people with difficulty entering text or using a mouse, and anyone facing an unfamiliar form.

**Common failures.** Complex forms (tax, benefits, job applications) with no explanations; help only available on a separate page that loses form data; help that is hard to discover.

**Related.** 3.3.2, 3.2.6, 3.1.3

=== 3.3.6
**Intent.** Help people avoid the consequences of mistakes when submitting **any** form data. It extends 3.3.4 from legal, financial and data-changing submissions to all submissions.

**At least one safeguard for every page where users submit information.**
- **Reversible:** submissions can be undone (e.g. edit or withdraw a sent message or application).
- **Checked:** input is checked for errors and the user can correct them.
- **Confirmed:** a mechanism to review, confirm and correct information before final submission.

**Practical approaches.** Client-side validation with clear messages before submission; a summary page for longer forms; the ability to edit or cancel submitted items afterwards; drafts that can be reviewed.

**Who benefits.** People with reading disabilities who transpose letters and numbers, people with motor disabilities who hit keys by mistake, people with cognitive disabilities who may have more difficulty detecting or recovering from mistakes.

**Common failures.** Contact, feedback or registration forms that submit immediately with no validation, review or way to correct afterwards.

**Related.** 3.3.4, 3.3.1, 3.3.3

=== 3.3.7
**Intent.** Make multi-step processes easier to complete by not asking users to re-enter information they already provided. Recalling earlier information taxes working memory and accelerates fatigue; people with cognitive and memory disabilities may give up or re-enter it incorrectly.

**What is required.** Information previously entered by or provided to the user, which is needed again **in the same process**, is either:
- **auto-populated**, or
- **available to select** — e.g. picked from a drop-down, copied from text shown on the same page, or filled by a checkbox like "Billing address same as delivery address". The data must be on the same page, ideally visible and close to the field (a show/hide area is acceptable).

**Scope.**
- A process is a single activity; there is no requirement to store information between sessions or after navigating away.
- A process can span domains — a third-party payment step within a checkout is in scope.
- Browser autofill does not count — the website must provide the data or avoid asking again.
- Not applicable when the information was supplied differently (e.g. uploading a CV document).
- After a failed submission, entered data should not be cleared.

**Exceptions.**
- **Essential:** re-entry is part of the purpose, e.g. a memory game.
- **Security:** e.g. confirming a newly created password that is not displayed.
- **No longer valid:** the earlier information has expired or changed.

**Privacy.** No special exception, but store data securely even temporarily during a process.

**Examples.** A purchase form shows the employee ID entered in step 1 as the default in step 3; a search results page pre-fills the search field; a checkout keeps the entered card number after an error.

**Who benefits.** People with cognitive, memory and learning disabilities, and people with mobility impairments using switch or voice input, for whom typing is slow.

**Common failures.** Asking for the email or address again in a later step; clearing all fields after a validation error; separate billing and delivery forms with no option to copy.

**Related.** 1.3.5, 3.3.8, 2.2.5

=== 3.3.8
**Intent.** Ensure there is an accessible, easy-to-use and secure way to log in to an existing account. Remembering usernames and passwords, transcribing one-time codes or solving puzzles is a very high or impossible burden for people with some cognitive disabilities.

**What is a cognitive function test.** Remembering (a password, a swipe pattern), transcribing (typing characters from one place to another, including audio CAPTCHAs), calculating, or solving puzzles.

**What is required.** No step of authentication requires a cognitive function test unless that step offers at least one of:
- **Alternative:** another method that is not a cognitive function test.
- **Mechanism:** help to complete the test — password managers and browser autofill, or copy and paste.
- **Object recognition:** e.g. "select all images with a car" (allowed at AA only; avoid if possible).
- **Personal content:** identifying an image, video or audio the user previously provided (text-based personal content does not qualify).

**Login forms.**
- Username/password logins pass if browsers and password managers can fill them — fields with correct `autocomplete` (1.3.5) and accessible names (4.1.2).
- They fail if scripts block autofill or **paste**, or if users must enter characters in a different format ("enter the 1st, 3rd and 5th characters of your password").
- Offering "show password" helps people who must type.

**Two-factor authentication.**
- Verification codes must be pasteable and fillable — not only typed manually. Six separate single-digit inputs that do not accept a pasted code fail.
- Moving a code from a phone to a computer is out of scope; assume it reaches the clipboard and check that paste works.
- Methods that are not cognitive tests: hardware keys (YubiKey), approving a push notification, passkeys/WebAuthn, platform biometrics (Windows Hello, Touch ID, Face ID), scanning a QR code, OAuth sign-in with another provider, magic links by email.

**Scope details.**
- Every step must have a compliant path, including account recovery.
- Applies to CAPTCHAs shown only sometimes (after failed attempts, with ad blockers).
- Logging in only; account creation is out of scope, though the same techniques help.
- Maths CAPTCHAs, logic puzzles and text CAPTCHAs are not excepted.

**Who benefits.** People with cognitive disabilities affecting memory, reading (dyslexia), numbers (dyscalculia) or processing, and anyone who struggles with complex logins.

**Common failures.** Paste blocked in password or code fields; `autocomplete="off"` with scripts preventing password managers; split one-time code inputs that reject paste; partial-password challenges; text or arithmetic CAPTCHAs with no alternative; security questions as the only recovery path.

**Related.** 3.3.9, 1.3.5, 3.3.7, 4.1.2, 1.1.1

=== 3.3.9
**Intent.** Ensure there is an accessible, easy-to-use and secure way to log in, access content and complete tasks — the same as 3.3.8, but **without** the exceptions for object recognition and personal content.

**What changes compared with 3.3.8.** Any required step of authentication:
- cannot ask users to pick which image, video or audio clip they previously provided;
- cannot ask users to select images containing a specific object (cars, traffic lights, animals).
These are still cognitive function tests, and some people with cognitive disabilities cannot complete them.

**Remaining ways to comply.**
- **Alternative** methods without cognitive tests: passkeys/WebAuthn, platform biometrics, hardware security keys, push-notification approval, magic links, OAuth sign-in.
- **Mechanisms** that assist: password managers, browser autofill, copy and paste of passwords and codes.

**Examples.** A login form that password managers fill automatically; paste allowed in all fields; WebAuthn login with fingerprint or face scan; 2FA by pressing a button on a USB key or approving a notification.

**Who benefits.** People with cognitive disabilities affecting memory, reading, numbers or processing — including those who cannot reliably recognise objects or their own images.

**Common failures.** Image-recognition CAPTCHAs ("select all squares with buses"); "pick the photo you uploaded" verification; any authentication step that relies on recall, transcription or puzzles with no alternative.

**Related.** 3.3.8, 1.3.5, 3.3.7

=== 4.1.1
**Status.** Obsolete and removed in WCAG 2.2. For WCAG 2.2 it is not evaluated; for WCAG 2.0 and 2.1, W3C errata state it is always satisfied for HTML and XML content.

**Original intent.** Ensure that user agents, including assistive technologies, could accurately parse content. In content implemented using markup languages: complete start and end tags, elements nested according to specifications, no duplicate attributes, unique IDs — except where the specifications allow otherwise. Different repair techniques in browsers and assistive technologies could otherwise produce different, broken results.

**Why it was removed.**
- HTML specifications now define precisely how to handle markup errors, and browsers parse consistently.
- Assistive technologies no longer parse HTML themselves; they use the accessibility tree built by the browser.
- So the original problems either no longer exist or are covered by other criteria.

**Where the real problems are now evaluated.**
- **Duplicate IDs** that break references — `<label for>`, `aria-labelledby`, `aria-describedby`, `headers` — so a field loses its label or description: **1.3.1** or **4.1.2**.
- **Improper nesting** that breaks semantics or roles (e.g. interactive elements inside each other, list items outside lists, required ARIA children missing): **1.3.1** or **4.1.2**.
- Issues that the specification allows are not failures at all.

**Practical advice.** Validating markup remains good engineering practice and helps catch errors that do affect accessibility, but invalid markup is not in itself a WCAG 2.2 failure. Audit the effects (names, roles, relationships), not the syntax.

**Who benefited.** Historically, screen reader users whose software parsed HTML directly.

**Common mistake in audits.** Reporting validator errors such as duplicate IDs or unclosed tags as failures of 4.1.1 in WCAG 2.2 audits; report them under 1.3.1 or 4.1.2 only if they cause an actual accessibility problem.

**Related.** 1.3.1, 4.1.2

=== 4.1.2
**Intent.** Ensure that assistive technologies — screen readers, magnifiers, speech recognition, switch software — can find out what each user interface component is, what it is called and what state it is in, can operate it, and are notified when that changes.

**The four parts.**
- **Name:** every component has a programmatically determinable name — from its content, a `<label>`, `alt`, `aria-label`, `aria-labelledby`, `title`, etc. Names may be visible (a label) or not, though visible labels are preferred (and 2.5.3 requires the visible text to be part of the name).
- **Role:** what the component is — button, link, checkbox, tab, slider, dialog, menu item.
- **States, properties and values:** checked/unchecked, expanded/collapsed, selected, pressed, disabled, required, invalid, the current value of a slider or combobox — and those the user can change must be settable programmatically.
- **Notification of changes:** when state or value changes (e.g. a disclosure opens, a tab is selected), assistive technology is informed. Focus is a key state.

**Native vs custom.**
- Standard HTML controls (`<button>`, `<a href>`, `<input>`, `<select>`, `<details>`) used according to specification meet this automatically.
- Custom widgets, or elements scripted to behave differently from their native role, need explicit semantics — usually WAI-ARIA roles, states and properties following the ARIA Authoring Practices patterns — plus scripts that keep states updated.
- First rule of ARIA: use a native element when one exists.
- Consider accessibility support: the roles and properties must actually work in the user's assistive technology.

**Scope.** All user interface components, including links, form fields and script-generated components. Page structure (headings, lists, tables) is 1.3.1; status messages are 4.1.3.

**Who benefits.** Screen reader users, speech recognition users who call controls by name, switch and other assistive technology users, and people using magnifiers that track focus.

**Common failures.**
- Icon-only buttons or links with no accessible name.
- Clickable `<div>`/`<span>` elements with no role (and usually no keyboard support).
- Custom checkboxes, toggles, tabs or accordions that do not expose or update `aria-checked`, `aria-pressed`, `aria-selected` or `aria-expanded`.
- Form fields without labels; iframes without titles.
- Incorrect roles (a link styled as a button that acts as a button, or `role="button"` on a link that navigates).
- Broken references from duplicate or missing IDs in `aria-labelledby`.

**Related.** 1.3.1, 2.5.3, 4.1.3, 1.1.1, 2.1.1, 3.3.2

=== 4.1.3
**Intent.** Make users aware of important status changes that do not receive focus, without unnecessarily interrupting their work. Sighted users notice text appearing elsewhere on the screen; screen reader users need it announced.

**What is a status message.** Both conditions must hold:
- It gives information on the **success or result of an action**, the **waiting state** of an application, the **progress** of a process, or the **existence of errors**.
- It is **not delivered through a change of context** (it does not take focus or load a new page).

**Examples of status messages.** "5 results returned" after a search; "Added to basket — 5 items"; "Invalid entry" appearing above a field; "Application busy" or a busy spinner; a progress bar for an upload; "Your form was successfully submitted"; "5 errors on page"; "Saved in 'Wedding' album".

**Not status messages (no action needed under this criterion).**
- Content that is the result itself, such as the list of search results.
- Errors shown in a dialog that takes focus — a change of context already announced.
- Content revealed by operating a component (menus, accordions, tabs, trees) — state changes are covered by 4.1.2.
- New form questions added based on an answer (helpful to announce, but not required).

**How to meet it.** Give the message a role or property that assistive technology announces, without moving focus:
- `role="status"` (polite) for results, confirmations and counts.
- `role="alert"` (assertive) for important, time-sensitive errors or warnings.
- `role="log"` for sequential updates such as chat; `role="progressbar"` for progress.
- `aria-live="polite"` or `"assertive"`, with `aria-atomic="true"` so the whole message is read ("3 items", not just "3").
- The live region should exist in the page before the message is inserted.

**Special cases.**
- Visual context may be missing: add visually hidden text ("3 items **in shopping cart**").
- When a "busy" message disappears, announce the new state ("System available").
- Icons or sounds signalling status need a text alternative (1.1.1) plus an appropriate role.

**Don't overdo it.** The criterion does not require creating new messages — only that displayed ones are exposed. Too many live announcements make an application "chatty"; test with users.

**Who benefits.** Blind and low-vision screen reader users; in future, people with cognitive disabilities whose assistive technology can delay, suppress or highlight messages.

**Common failures.** "Saved", "Added to cart" or "Copied" toasts that appear silently; search result counts not announced; inline validation errors inserted without a live region or focus change; loading indicators without an accessible status.

**Related.** 4.1.2, 3.3.1, 1.1.1, 2.2.4


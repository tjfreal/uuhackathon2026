on readUtf8File(posixPath)
	return do shell script "/bin/cat " & quoted form of posixPath
end readUtf8File

on replaceLiteral(sourceText, findText, replaceText)
	set AppleScript's text item delimiters to findText
	set textItems to text items of sourceText
	set AppleScript's text item delimiters to replaceText
	set replacedText to textItems as text
	set AppleScript's text item delimiters to ""
	return replacedText
end replaceLiteral

on decodeEscapes(sourceText)
	set decodedText to my replaceLiteral(sourceText, "\\n", return)
	set decodedText to my replaceLiteral(decodedText, "\\t", tab)
	return decodedText
end decodeEscapes

on trimText(sourceText)
	set trimmedText to sourceText
	repeat while trimmedText is not "" and (trimmedText begins with space or trimmedText begins with tab)
		set trimmedText to text 2 thru -1 of trimmedText
	end repeat
	repeat while trimmedText is not "" and (trimmedText ends with space or trimmedText ends with tab)
		set trimmedText to text 1 thru -2 of trimmedText
	end repeat
	return trimmedText
end trimText

on configValue(configText, keyName, defaultValue)
	repeat with rawLine in paragraphs of configText
		set currentLine to my trimText(contents of rawLine)
		if currentLine is not "" and currentLine does not start with "#" then
			set AppleScript's text item delimiters to "="
			set parts to text items of currentLine
			set AppleScript's text item delimiters to ""
			if (count of parts) is greater than or equal to 2 then
				set currentKey to my trimText(item 1 of parts)
				if currentKey is keyName then
					set AppleScript's text item delimiters to "="
					set rawValue to items 2 thru -1 of parts as text
					set AppleScript's text item delimiters to ""
					return my trimText(rawValue)
				end if
			end if
		end if
	end repeat
	return defaultValue
end configValue

on parseSlides(slidesText)
	set slideList to {}
	repeat with rawLine in paragraphs of slidesText
		set currentLine to my trimText(contents of rawLine)
		if currentLine is not "" and currentLine does not start with "#" then
			set AppleScript's text item delimiters to "|||"
			set parts to text items of currentLine
			set AppleScript's text item delimiters to ""
			if (count of parts) is greater than or equal to 4 then
				set end of slideList to {layoutName:my trimText(item 1 of parts), titleText:my decodeEscapes(my trimText(item 2 of parts)), bodyText:my decodeEscapes(my trimText(item 3 of parts)), notesText:my decodeEscapes(my trimText(item 4 of parts))}
			end if
		end if
	end repeat
	return slideList
end parseSlides

on setTitleBodyAndNotes(docRef, slideRef, layoutName, titleText, bodyText, notesText)
	tell application "Keynote"
		tell docRef
			tell slideRef
				set base layout to master slide layoutName of docRef
			end tell
		end tell
		tell slideRef
			try
				set object text of default title item to titleText
			end try
			try
				set object text of default body item to bodyText
			end try
			if notesText is not "" then
				try
					set presenter notes to notesText
				end try
			end if
		end tell
	end tell
end setTitleBodyAndNotes

on addSlide(docRef, layoutName, titleText, bodyText, notesText)
	tell application "Keynote"
		tell docRef
			set slideRef to make new slide
		end tell
	end tell
	my setTitleBodyAndNotes(docRef, slideRef, layoutName, titleText, bodyText, notesText)
	return slideRef
end addSlide

set outputDir to "__SET_THIS_TO_THE_DECK_PACKAGE_DIRECTORY__"
set configPath to outputDir & "/deck_config.txt"
set configText to my readUtf8File(configPath)

set deckName to my configValue(configText, "deck_name", "deck")
set themeName to my configValue(configText, "theme", "Bold Color")
set deckWidth to (my configValue(configText, "width", "1920")) as integer
set deckHeight to (my configValue(configText, "height", "1080")) as integer
set slidesFileName to my configValue(configText, "slides_file", "slides.txt")

set slidesPath to outputDir & "/" & slidesFileName
set slidesText to my readUtf8File(slidesPath)
set slideSpecs to my parseSlides(slidesText)

set deckPath to POSIX file (outputDir & "/" & deckName & ".key")
set pptxPath to POSIX file (outputDir & "/" & deckName & ".pptx")

tell application "Keynote"
	activate
	set docRef to make new document with properties {document theme:theme themeName}
	tell docRef
		set width to deckWidth
		set height to deckHeight
	end tell
	
	if (count of slideSpecs) > 0 then
		set firstSpec to item 1 of slideSpecs
		set firstSlide to current slide of docRef
		my setTitleBodyAndNotes(docRef, firstSlide, layoutName of firstSpec, titleText of firstSpec, bodyText of firstSpec, notesText of firstSpec)
		
		repeat with i from 2 to count of slideSpecs
			set currentSpec to item i of slideSpecs
			my addSlide(docRef, layoutName of currentSpec, titleText of currentSpec, bodyText of currentSpec, notesText of currentSpec)
		end repeat
	end if
	
	tell docRef
		save in deckPath
		export to pptxPath as Microsoft PowerPoint
	end tell
end tell

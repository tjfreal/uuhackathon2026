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

on basenameForPath(posixPath)
	return do shell script "/usr/bin/basename " & quoted form of posixPath
end basenameForPath

on imageDimensions(posixPath)
	set shellCmd to "/usr/bin/sips -g pixelWidth -g pixelHeight " & quoted form of posixPath & " | /usr/bin/awk '/pixelWidth:/ {w=$2} /pixelHeight:/ {h=$2} END {print w \"x\" h}'"
	return do shell script shellCmd
end imageDimensions

on imageMetadataNotes(posixPath)
	set filenameText to my basenameForPath(posixPath)
	set dimensionsText to my imageDimensions(posixPath)
	set statCmd to "/usr/bin/stat -f 'Size bytes: %z" & linefeed & "Modified: %Sm' -t '%Y-%m-%d %H:%M:%S' " & quoted form of posixPath
	set statText to do shell script statCmd
	return "Filename: " & filenameText & linefeed & "Path: " & posixPath & linefeed & "Dimensions: " & dimensionsText & linefeed & statText
end imageMetadataNotes

on resolveImagePath(imagePath, imageRoot)
	if imagePath is "" then return ""
	if imagePath starts with "/" then return imagePath
	if imageRoot is "" then return imagePath
	if imageRoot ends with "/" then
		return imageRoot & imagePath
	else
		return imageRoot & "/" & imagePath
	end if
end resolveImagePath

on parseSlides(slidesText)
	set slideList to {}
	repeat with rawLine in paragraphs of slidesText
		set currentLine to my trimText(contents of rawLine)
		if currentLine is not "" and currentLine does not start with "#" then
			set AppleScript's text item delimiters to "|||"
			set parts to text items of currentLine
			set AppleScript's text item delimiters to ""
			if (count of parts) is greater than or equal to 4 then
				set imagePathText to ""
				set imageLayoutText to ""
				if (count of parts) is greater than or equal to 5 then set imagePathText to my trimText(item 5 of parts)
				if (count of parts) is greater than or equal to 6 then set imageLayoutText to my trimText(item 6 of parts)
				set end of slideList to {layoutName:my trimText(item 1 of parts), titleText:my decodeEscapes(my trimText(item 2 of parts)), bodyText:my decodeEscapes(my trimText(item 3 of parts)), notesText:my decodeEscapes(my trimText(item 4 of parts)), imagePathText:imagePathText, imageLayoutText:imageLayoutText}
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

on addImageToSlide(slideRef, imagePath, deckWidth, deckHeight, imageLayout)
	set imageAlias to POSIX file imagePath
	set dimensionsText to my imageDimensions(imagePath)
	set AppleScript's text item delimiters to "x"
	set dimensionParts to text items of dimensionsText
	set AppleScript's text item delimiters to ""
	if (count of dimensionParts) is less than 2 then return
	set imageWidthPx to (item 1 of dimensionParts) as real
	set imageHeightPx to (item 2 of dimensionParts) as real
	
	set normalizedLayout to imageLayout
	if normalizedLayout is "" then set normalizedLayout to "center"
	
	if normalizedLayout is "full" then
		set leftMargin to 40
		set rightMargin to 40
		set topMargin to 120
		set bottomMargin to 40
	else if normalizedLayout is "sidebar-right" or normalizedLayout is "sidebar-left" then
		set leftMargin to 80
		set rightMargin to 80
		set topMargin to 150
		set bottomMargin to 70
	else
		set leftMargin to 120
		set rightMargin to 120
		set topMargin to 150
		set bottomMargin to 70
	end if
	
	if normalizedLayout is "sidebar-right" or normalizedLayout is "sidebar-left" then
		set maxWidth to deckWidth * 0.34
	else
		set maxWidth to deckWidth - leftMargin - rightMargin
	end if
	set maxHeight to deckHeight - topMargin - bottomMargin
	set widthRatio to maxWidth / imageWidthPx
	set heightRatio to maxHeight / imageHeightPx
	if widthRatio < heightRatio then
		set scaleRatio to widthRatio
	else
		set scaleRatio to heightRatio
	end if
	set finalWidth to imageWidthPx * scaleRatio
	set finalHeight to imageHeightPx * scaleRatio
	if normalizedLayout is "sidebar-right" then
		set imageX to deckWidth - rightMargin - finalWidth
	else if normalizedLayout is "sidebar-left" then
		set imageX to leftMargin
	else
		set imageX to (deckWidth - finalWidth) / 2
	end if
	set imageY to topMargin + ((maxHeight - finalHeight) / 2)
	
	tell application "Keynote"
		tell slideRef
			set imageRef to make new image with properties {file:imageAlias}
			set width of imageRef to finalWidth
			set height of imageRef to finalHeight
			set position of imageRef to {imageX, imageY}
		end tell
	end tell
end addImageToSlide

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
set imageRoot to my configValue(configText, "image_root", "")

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
		set firstImagePath to my resolveImagePath(imagePathText of firstSpec, imageRoot)
		set firstNotesText to notesText of firstSpec
		if firstImagePath is not "" then set firstNotesText to firstNotesText & linefeed & linefeed & my imageMetadataNotes(firstImagePath)
		my setTitleBodyAndNotes(docRef, firstSlide, layoutName of firstSpec, titleText of firstSpec, bodyText of firstSpec, firstNotesText)
		if firstImagePath is not "" then my addImageToSlide(firstSlide, firstImagePath, deckWidth, deckHeight, imageLayoutText of firstSpec)
		
		repeat with i from 2 to count of slideSpecs
			set currentSpec to item i of slideSpecs
			set currentImagePath to my resolveImagePath(imagePathText of currentSpec, imageRoot)
			set currentNotesText to notesText of currentSpec
			if currentImagePath is not "" then set currentNotesText to currentNotesText & linefeed & linefeed & my imageMetadataNotes(currentImagePath)
			set slideRef to my addSlide(docRef, layoutName of currentSpec, titleText of currentSpec, bodyText of currentSpec, currentNotesText)
			if currentImagePath is not "" then my addImageToSlide(slideRef, currentImagePath, deckWidth, deckHeight, imageLayoutText of currentSpec)
		end repeat
	end if
	
	tell docRef
		save in deckPath
		export to pptxPath as Microsoft PowerPoint
	end tell
end tell

# import the main rules
import basic

while True:
	text = input('>>> ')
	# we should be able to get the result and error
	# and call the run function from the imported file, take in a file name and pass in the text
	if text.strip() == "": continue
	result, error = basic.run('<stdin>', text)

	if error:
		# if any error is found 
		# then we call the function that creates a string that shows the error's name, and other details
		print(error.as_string())
	elif result:
		if len(result.elements) == 1:
			print(repr(result.elements[0]))
		else:
			print(repr(result))
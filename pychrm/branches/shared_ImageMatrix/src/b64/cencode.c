/*
cencoder.c - c source to a base64 encoding algorithm implementation

This is part of the libb64 project, and has been placed in the public domain.
For details, see http://sourceforge.net/projects/libb64

modified to use file/URL safe alphabet (base64url) as proposed in RFC 4648:
	character 62 (0x3E, '+') is replaced with a "-" (minus sign)
	character 63 (0x3F) '/') is replaced with a "_" (underscore).
*/

#include <b64/cencode.h>

void base64_init_encodestate(base64_encodestate* state_in, char newlines, char padding)
{
	state_in->step = step_A;
	state_in->result = 0;
	state_in->stepcount = 0;
	state_in->chars_per_line = (newlines ? 72 : 0);
	state_in->use_padding = (padding ? 1 : 0);
}

char base64_encode_value(char value_in)
{
	static const char* encoding = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
	if (value_in > 63) return '=';
	return encoding[(int)value_in];
}

size_t base64_encode_block(const char* plaintext_in, size_t length_in, char* code_out, base64_encodestate* state_in)
{
	const char* plainchar = plaintext_in;
	const char* const plaintextend = plaintext_in + length_in;
	char* codechar = code_out;
	char result;
	char fragment;
	
	result = state_in->result;
	
	switch (state_in->step)
	{
		while (1)
		{
	case step_A:
			if (plainchar == plaintextend)
			{
				state_in->result = result;
				state_in->step = step_A;
				return codechar - code_out;
			}
			fragment = *plainchar++;
			result = (fragment & 0x0fc) >> 2;
			*codechar++ = base64_encode_value(result);
			result = (fragment & 0x003) << 4;
	case step_B:
			if (plainchar == plaintextend)
			{
				state_in->result = result;
				state_in->step = step_B;
				return codechar - code_out;
			}
			fragment = *plainchar++;
			result |= (fragment & 0x0f0) >> 4;
			*codechar++ = base64_encode_value(result);
			result = (fragment & 0x00f) << 2;
	case step_C:
			if (plainchar == plaintextend)
			{
				state_in->result = result;
				state_in->step = step_C;
				return codechar - code_out;
			}
			fragment = *plainchar++;
			result |= (fragment & 0x0c0) >> 6;
			*codechar++ = base64_encode_value(result);
			result  = (fragment & 0x03f) >> 0;
			*codechar++ = base64_encode_value(result);
			
			++(state_in->stepcount);
			if (state_in->chars_per_line && state_in->stepcount == state_in->chars_per_line/4)
			{
				*codechar++ = '\n';
				state_in->stepcount = 0;
			}
		}
	}
	/* control should not reach here */
	return codechar - code_out;
}

size_t base64_encode_blockend(char* code_out, base64_encodestate* state_in)
{
	char* codechar = code_out;
	
	switch (state_in->step)
	{
	case step_B:
		*codechar++ = base64_encode_value(state_in->result);
		if (state_in->use_padding) {
			*codechar++ = '=';
			*codechar++ = '=';
		}
		break;
	case step_C:
		*codechar++ = base64_encode_value(state_in->result);
		if (state_in->use_padding)
			*codechar++ = '=';
		break;
	case step_A:
		break;
	}
	if (state_in->chars_per_line) *codechar++ = '\n';
	
	return codechar - code_out;
}


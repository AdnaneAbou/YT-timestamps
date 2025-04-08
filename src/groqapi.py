import os 
import time
from groq import Groq
from dotenv import load_dotenv
# from prompt import Prompt
import re
from transformers import AutoTokenizer

class GroqTimestampGenerator:
    def __init__(self):
        load_dotenv()
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama3-70b-8192"
        self.max_content_tokens = 7168
        self.tpm_limit = 6000

    def generate_timestamps(self, transcript , prompt_template , video_url=""):
        """Main method to generate timestamps for long transcripts"""
        try:

            if not transcript or len(transcript) < 100:
                return "Error : Transcript too short or empty"
            
            chunks = self._chunk_transcript(transcript)

            return self._process_chunks(chunks,prompt_template,video_url)
        
        except Exception as e:
            return f"Critical Error: {str(e)}"
        
    def chunk_transcript(self,text):
        """Token-aware chunking with overlap for context continuity"""

        tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
        tokens = tokenizer.encode(text)

        chunk_size = self.max_content_tokens
        overlap = int(chunk_size * 0.1)
        step_size = chunk_size - overlap
        
        chunks = []
        i = 0
        while i < len(tokens):
            # Align to nearest sentence boundary within 50 tokens
            end = min(i + chunk_size, len(tokens))
            lookback = min(50, end - i)
            
            # Find natural break point
            for adj in range(lookback):
                if tokenizer.decode([tokens[end-adj-1]]).endswith(('.', '!', '?')):
                    end = end - adj
                    break
                    
            chunks.append(tokenizer.decode(tokens[i:end]))
            i = max(i + step_size, end - overlap)  # Ensure minimum overlap
        
        return chunks
    

    def _process_chunks(self , chunks,prompt_template, video_url ):
        """Process chunks with rate limiting and error handling"""

        full_response = []
        tokens_used = 0
        window_start = time.time()

        for i, chunk  in enumerate(chunks):
            try:
                # Rate limiting check
                tokens_used, window_start = self._enforce_rate_limit(tokens_used, window_start)
                
                # Create enhanced prompt
                prompt = self._build_prompt(prompt_template, chunk,chunks, len(chunks))
                
                # API call with retries
                response = self._safe_api_call(prompt)
                
                if response:
                    full_response.append(response)
                    print(f"Processed chunk {i+1}/{len(chunks)} successfully")
                
            except Exception as e:
                print(f"Error processing chunk {i+1}: {str(e)}")
                continue
                
        return "\n\n".join(full_response) if full_response else "No timestamps generated"

            
    def _build_prompt(self , template, chunk_num , chunks, total_chunks):
        """Construct context-aware prompt with chunk position info"""

        return f"""{template}
        
         CONTEXT AWARENESS:
        - You are processing chunk {chunk_num}/{total_chunks}
        - Previous chunks ended with :{self._get_previous_context(chunks,chunk_num)} [brief summary]
        - NEVER repeat timestamps from earlier chunks
        - Use [CONTINUED] only when essential
        """
    
    def _safe_api_call(self, prompt):
        """API Call with timeout and validation"""

        try:
            response = self.client.chat.completions.create(
                messages=[{"role":"system",
                           "content":prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1024,
                timeout=30
            )

            if response and response.choices:
                content = response.choices[0].message.content
                return content.strip() if content else None
            
            return None

        except Exception as e :
            return f"API ERROR : {str(e)}"


    def _enforce_rate_limit(self, tokens_used ,window_start):
        """Intelligent rate limiting with dynamic backoff"""

        elapsed = time.time() - window_start
        if elapsed < 0.001:
            return tokens_used,window_start
        
        current_tpm = tokens_used / (elapsed / 60)
        
        if current_tpm > self.tpm_limit *0.95 :
            sleep_time = 60 - elapsed
            print(f"⚠️ Approaching rate limit. Cooling down {sleep_time:.1f}s")
            time.sleep(max(sleep_time,0))
            return 0, time.time()
        
        return tokens_used, window_start
  
    def _get_previous_context(self, chunks,current_index):
        """Get last 50 words of previous chunk"""
        if current_index <= 1:
            return "Beginning of transcript"
        return ' '.join(chunks[current_index-2].split()[-50:])


    def _deduplicate_result(self,text):
        """Remove duplicates timestamp entries"""

        seen =set()
        clean_lines = []
        for line in text.split('\n'):
            if "?t=" in line and line not in seen:
                seen.add(line)
                clean_lines.append(line)
        return 'n'.join(clean_lines)
    



def validate_response(response):
    """Check for valid timestamp URLs"""
    pattern = r"\?t=\d+"
    matches = re.findall(pattern, response)
    return len(matches) > 0  # True if valid timestamps exist


if __name__ == "__main__":

    with open("official_transcript.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()


    # Initialize with your formatted transcript
    # generator = GroqTimestampGenerator()
    # result = generator.generate_timestamps(
    #     transcript=raw_text,
    #     prompt_template=Prompt.prompt1(ID='timestamp'),  # Updated with conversion rules
    #     video_url="https://www.youtube.com/watch?v=9p3HbNuljS4"
    # )
    # # Validate output
    # if validate_response(result):
    #     print("Valid timestamps generated:\n", result)
    # else:
    #     print("⚠️ Regenerate with stricter prompt instructions")

    # Generate a transcript longer than chunk_size * 1.5

    # test_transcript = ("Sample content " * 20000).strip()  # ~20k tokens
    def test_overlapping_chunks(test_transcript):
        generator = GroqTimestampGenerator()
        
        # Test configuration
        # Generate chunks
        chunks = generator.chunk_transcript(
            text=test_transcript)
        
        
        # print(f"Here are the Chunk number one ", chunks[0] , end='\n')
        # print(f"Here are the Chunk number 2 ", chunks[1] , end='\n')

        # Validate chunk count
        print(f"Total chunks: {len(chunks)}")
        if len(chunks) < 2:
            raise ValueError("Test transcript too short - needs 2+ chunks")
        
        # Check overlap between first two chunks
        chunk1_end = chunks[0][-1000:]  # Last 500 characters of chunk 1
        chunk2_start = chunks[1][:1000] # First 500 characters of chunk 2
        
        print("\nChunk 1 End:\n", chunk1_end)
        print("\nChunk 2 Start:\n", chunk2_start)
        
        # Calculate overlap percentage
        overlap_chars = len(os.path.commonprefix([chunk1_end[::-1], chunk2_start[::-1]]))
        total_chars = len(chunks[0])
        overlap_pct = (overlap_chars / total_chars) * 100
        
        print(f"\nOverlap: {overlap_pct:.1f}% (should be ~10%)")
    # Run test
    test_overlapping_chunks(raw_text)
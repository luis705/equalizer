run:
	python main.py

format:
	isort *.py	
	blue *.py

test:
	python validation/generate_sweep.py
	python analyzer.py -p profiles/a.json -i validation/chirp.wav -o validation/sweep_out.mp4 -a out
	python analyzer.py -p profiles/a.json -i validation/chirp.wav -o validation/sweep_in.mp4 -a in

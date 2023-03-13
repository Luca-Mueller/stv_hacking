import numpy as np
import time


def read_data():
	raw_data = None
	with open('data.toi', 'r') as f:
		raw_data = f.read()
	return raw_data


def parse_data(raw_data):
	ballots = []
	for line in raw_data.split('\n'):
		if line.startswith('#'):
			continue
		
		n_votes, alternatives = line.split(':')
		n_votes, alternatives = n_votes.strip(), alternatives.strip()
		
		pos = 1
		hold = False
		ranks = np.zeros(11, dtype=np.int32)
		for a in alternatives.split(','):
			if a.startswith('{'):
				hold = True

			if a.endswith('}'):
				hold = False

			a = int(a.strip('{').strip('}'))
			ranks[a-1] = pos

			if not hold:
				pos += 1

		ballots.append((int(n_votes), ranks))

	return ballots


def stv(ballots):
	qualified = np.ones(11)
	qualified_last_round = qualified

	def get_top_votes(ballots):
		top_votes = np.zeros(11, dtype=np.int32)
		for b in ballots:
			n_votes, ranks = b
			try:
				top_choice = np.where(ranks == np.min(ranks[ranks * qualified != 0]))
				top_votes[top_choice] += n_votes
			except ValueError:
				# means no valid vote, ignore ballot
				pass

		return top_votes
 
	while np.sum(qualified):
		votes = get_top_votes(ballots)
		eliminate = np.where(votes == np.min(votes[np.where(qualified)]))
		qualified_last_round = qualified.copy()
		qualified[eliminate] = 0

	return np.where(qualified_last_round)[0] + 1


# find the alternative which is ranked above 'a' most frequently
def  better_than(a, ballots):
	better_than_a = np.zeros(11)
	ballots_fixed, ballots_manip = [], []
	for b in ballots:
		n_votes, ranks = b
		manip = False
		for idx, rank in enumerate(ranks):
			# a ballot can be manipulated if a non-winning alternative is ranked above 'a'
			if rank and idx != (a-1) and ((ranks[idx] < ranks[a-1]) or not ranks[a-1]):
				better_than_a[idx] += n_votes
				manip = True

		if manip:
			# ballots that can potentially be manipulated
			ballots_manip.append(b)
		else:
			# ballots which cannot be manipulated
			ballots_fixed.append(b)

	return np.argmax(better_than_a) + 1, ballots_fixed, ballots_manip


def hack_election(winners, candidate, ballots_fixed, ballots_manip):
	def split_ballots(ballots):
		# split ballots so there is one voter per ballot
		new_ballots = []
		for b in ballots:
			n_votes, ranks = b
			for v in range(n_votes):
				new_ballots.append((1, ranks))

		return new_ballots

	def can_manipulate(winners, candidate, ballot):
		n_votes, ranks = ballot
		if ranks[candidate-1] == 1 or ranks[candidate-1] == 0:
			# cannot maniputlate if candidate is already ranked highest
			# or candidate is not ranked at all
			return False
		for w in winners:
			if ranks[w-1] and ranks[w-1] < ranks[candidate-1]:
				# cannot manipulate if winner is ranked higher than candidate
				return False

		return True

	ballots_manip = split_ballots(ballots_manip)
	n_ballots = len(ballots_manip) + len(split_ballots(ballots_fixed))

	skipped = 0
	manipulated = []
	for n in range(len(ballots_manip)):
		print(f'\r[*] Manipulating {n-skipped:>4}/{n_ballots:<4} ballots', end='')

		# change n ballots
		if not can_manipulate(winners, candidate, ballots_manip[n]):
			# candidate is already top choice, is not in ballot or is ranked lower than winner
			skipped += 1
			continue
		else:
			# switch ranks of candidate and top choice
			manipulated.append(ballots_manip[n][1].copy())
			switch_with = np.where(ballots_manip[n][1] == 1)
			ballots_manip[n][1][switch_with] = ballots_manip[n][1][candidate-1]
			ballots_manip[n][1][candidate-1] = 1

		# get stv winner
		ballots_n = ballots_fixed + ballots_manip
		winners_n = stv(ballots_n)
		# if new winner != winner, break
		if winners_n != winners:
			print(f'\n[+] Election hacked with {n-skipped+1} votes, new winner(s): {winners_n}')
			print('[i] Manipulated ballots:\nvvv')
			for b in manipulated:
				print(b)
			print('^^^')
			return (n - skipped + 1), winners_n

	print('\n[-] Could not hack election')


if __name__ == '__main__':
	start = time.time()
	raw_data = read_data()
	ballots = parse_data(raw_data)
	winners = stv(ballots)
	middle = time.time()
	print(f'Time passed until a winner is found using STV method: {middle - start}\n')
	print(f'[+] Election winner(s):\t{winners}')
	candidate, ballots_fixed, ballots_manip = better_than(winners[0], ballots)
	print(f'[+] Candidate:\t\t{candidate}')
	hack_election(winners, candidate, ballots_fixed, ballots_manip)
	end = time.time()
	print(f'Time passed until the hacking of the election is done: {end - start}')

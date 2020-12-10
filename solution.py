from Pyro4 import expose

class Solver:

    def __init__(self, workers=None, input_file_name=None, output_file_name=None):
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        self.workers = workers

    def read_input(self):
        f = open(self.input_file_name, 'r')
        a = [list(map(float, line.split())) for line in f]
        f.close()
        return a


    @expose
    def load_data(self, data, start, end):
        self.start = start
        self.end = end
        self.n = len(data[0])
        self.data = data
        for i in range(end-start):
            self.data[i]+=[0.]*self.n
            self.data[i][self.n+start+i]=1.

    @expose
    def save_data(self):
        for i in range(self.end-self.start):
            d = 1./self.data[i][i+self.start]
            self.data[i] = [x*d for x in self.data[i][self.n:]]
        return self.data

    @expose
    def get_row(self, i):
        return self.data[i-self.start]

    @expose
    def subtract(self, i, row):
        for k in range(self.end-self.start):
            j = k+self.start
            if i != j:
                ratio = self.data[k][i]/row[i]
                for l in range(2*self.n):
                    self.data[k][l] -= ratio * row[l]

    def solve(self):
        A = self.read_input()
        count = len(self.workers)
        n = len(A[0])

        ### prepare data to workers
        rows_on_worker = n//count
        mapped = [None]*count
        for i in range(count):
            start = i*rows_on_worker
            end = (i+1)*rows_on_worker
            mapped[i] = self.workers[i].load_data(A[start:end],start,end)
        for x in mapped:
            x.value
        
        ###inversion
        for i in range(n):
            row = self.workers[i//rows_on_worker].get_row(i).value
            if row[i] == 0.:
                return None
            for j in range(count):
               mapped[j] = self.workers[j].subtract(i, row)
            for x in mapped:
                x.value
        ### getting data from workers and output it
        mapped = [self.workers[i].save_data() for i in range(count)]
        for i in range(count):
            start = i*rows_on_worker
            end = (i+1)*rows_on_worker
            A[start:end]=mapped[i].value
        self.write_output(A)

    def write_output(self, output):
        f = open(self.output_file_name, 'w')
        for line in output:
            f.write(" ".join(map(str, line)))
            f.write('\n')
        f.close()

def main():
    workers = [Solver() for i in range(4)]
    manager = Solver(workers, 'D:\\parcs proj\\input', 'D:\\parcs proj\\output')
    manager.solve()

###main()
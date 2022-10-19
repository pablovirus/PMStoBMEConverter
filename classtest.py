class Channel:

    def __init__(self, name, length, channel, lcm):
        self.name = name
        self.length = length
        self.contents = ['00' for i in range(length)]
        self.channel = channel
        self.lcm = lcm

    def __repr__(self):
        return f' Channel name: {self.name}'
    
    def print_contents(self):
        print(self.contents)

    def modify_sample(self, sample_position: int, sample: str) -> None:
        '''Modify a single sample at a given position'''
        self.contents[sample_position] = sample

    def modify_range(self, start: int, end: int, values: list[str]):
        '''Modify a samples at a given range'''
        self.contents[start:end] = values

    def read_sample(self, sample_position: int) -> str:
        '''Read a single sample at a given position'''
        return self.contents[sample_position]
    
    def read_range(self, start: int, end: int) -> list[str]:
        '''Read samples in a given range'''
        return self.contents[start:end]

    def count_non_null_samples(
            self, 
            begin: int, 
            end: int, 
            null_sample: str = '00') -> int:
        '''Count non-null samples within a given range. You can specify the null sample'''
        count = 0
        for element in self.contents[begin : end]:
            if element != null_sample:
                count += 1
        return count

    def convert_to_string(self) -> str:
        '''Convert contents of this channel to BMS format'''
        content_as_str = ''.join(self.contents)
        divided = [
            (content_as_str[i:i+self.lcm*2]) 
            for i in range(0, len(content_as_str), self.lcm*2)
            ]
        output = ''
        for ind, measure in enumerate(divided):
            output = output + '#' + str(ind).zfill(3) + self.channel + ':' + measure + '\n'
        return output


def main():
    channel_test = Channel('MC1', length=64*6, lcm=64, channel='17')
    print(channel_test)
    channel_test.modify_sample(3, 'AA')
    print(channel_test.count_non_null_samples(begin=7, end=9))
    print('Converted to string:')
    print(channel_test.convert_to_string())

if __name__ == '__main__':
    main()
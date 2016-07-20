from support import load_tickets, load_default_limits


def update_data():
    print 'loading default limits...'
    load_default_limits()
    print 'loading tickets...'
    load_tickets()
    print 'done'

if __name__ == "__main__":
    update_data()


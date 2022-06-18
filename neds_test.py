###
# Get odds from NEDS
###
from utils import choose_lay_option

if __name__ == "__main__":
    venueName = 'doncaster'
    lay_option = choose_lay_option(venueName)
    if(lay_option == -1):
        print("ERROR!!! 2 same odds found")
        
    elif(lay_option == -2):
        print("ERROR!!! less than 6 runners")

    else:
        print("Lay option found successfully")
        print(lay_option)




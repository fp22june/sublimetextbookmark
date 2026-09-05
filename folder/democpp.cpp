#include <iostream>
#include <string>
class Car {
private:
    std::string brand;
    int speed;
public:
    Car(std::string carBrand, int initialSpeed) {
        brand = carBrand;
        speed = initialSpeed;
    }
    void displayInfo() {
        std::cout << "Car Brand: " << brand << " | Current Speed: " << speed << " km/h" << std::endl;
    }
    void accelerate(int increase);
};
void Car::accelerate(int increase) {
    speed += increase;
    std::cout << brand << " accelerated by " << increase << " km/h." << std::endl;
}
int main() {
    Car myCar("Toyota", 60);
    myCar.displayInfo();
    myCar.accelerate(30);
    myCar.displayInfo();
    return 0;
}
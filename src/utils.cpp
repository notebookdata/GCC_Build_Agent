#include "../include/matrix.hpp"
#include <iostream>

void printMatrixInfo(const Matrix<int>& m) {
    std::cout << "Matrix dimensions: " << m.getRows() << "x" << m.getCols() << std::endl;
}

// Implementation of the missing function
void specializedSolver(const Matrix<float>& m) {
    // Example implementation: Print matrix information
    std::cout << "Specialized solver for float matrix with dimensions: "
              << m.getRows() << "x" << m.getCols() << std::endl;

    // Add your specific logic here
}
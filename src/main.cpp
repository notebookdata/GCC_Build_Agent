#include "../include/matrix.hpp"
#include <string>

int main() {
    Matrix<int> mat1(3, 3);
    mat1.setValue(0, 0, 10);

    Matrix<int> mat2(3, 3);
    mat2.setValue(0, 0, 5);

    mat1.add(mat2);

    printMatrixInfo(mat1);

    // --- Complex Template Error ---
    // Instantiating Matrix with std::string, but the 'add' function 
    // uses += which might work for strings, but let's see if the AI catches context.
    Matrix<std::string> strMat(2, 2);
    strMat.setValue(0, 0, "Hello");

    // ERROR 5: Linker Error
    // This function is declared in the header but implemented NOWHERE.
    // The compiler will pass, but the Linker (ld) will fail.
    Matrix<float> fMat(2, 2);
    specializedSolver(fMat);

    return 0;
}

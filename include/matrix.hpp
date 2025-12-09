#ifndef MATRIX_HPP
#define MATRIX_HPP

#include <vector>
#include <iostream>

template <typename T>
class Matrix {
private:
    std::vector<std::vector<T>> data;
    int rows, cols;

public:
    Matrix(int r, int c) : rows(r), cols(c) {
        data.resize(r, std::vector<T>(c));
    }

    void setValue(int r, int c, T val) {
        data[r][c] = val;
    }

    T getValue(int r, int c) const {
        return data[r][c];
    }

    // Added getter methods for rows and cols
    int getRows() const {
        return rows;
    }

    int getCols() const {
        return cols;
    }

    void add(const Matrix<T>& other) {
        for (int i = 0; i < rows; ++i) {
            for (int j = 0; j < cols; ++j) {
                data[i][j] += other.data[i][j];
            }
        }
    }
};

// Declaration of a function defined in utils.cpp
void printMatrixInfo(const Matrix<int>& m);

// Declaration of a function that is NEVER defined (Linker Error)
void specializedSolver(const Matrix<float>& m);

#endif
#ifndef COMPACT_STRUCTURE_H
#define COMPACT_STRUCTURE_H

#include "descriptor.h"
#include "structure.h"
#include <vector>

class CompactStructure : public Structure {
public:
  int n_species, n_descriptors;
  Eigen::VectorXi neighbor_count, cumulative_neighbor_count, structure_indices,
      neighbor_species;
  Eigen::MatrixXd relative_positions;
  double cutoff;
  int sweep, n_neighbors;

  // Store descriptor information.
  // TODO: Store these attributes inside descriptor class.
  Eigen::VectorXi species_indices;
  std::vector<Eigen::MatrixXd> descriptors, descriptor_force_dervs,
    neighbor_coordinates;
  std::vector<Eigen::VectorXd> descriptor_norms, descriptor_force_dots;
  std::vector<Eigen::VectorXi> neighbor_counts, cumulative_neighbor_counts,
      atom_indices, neighbor_indices;
  std::vector<int> n_atoms_by_species, n_neighbors_by_species;
  DescriptorCalculator *descriptor_calculator;

  CompactStructure();

  CompactStructure(const Eigen::MatrixXd &cell, const std::vector<int> &species,
                   const Eigen::MatrixXd &positions, double cutoff,
                   DescriptorCalculator *descriptor_calculator);

  void compute_neighbors();
  void compute_descriptors();
};

#endif
